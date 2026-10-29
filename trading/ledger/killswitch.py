"""trading/ledger/killswitch.py — persistent, fail-closed kill switch.

Scopes: GLOBAL ("*"), SYMBOL (e.g. "BTCUSDT"), STRATEGY (strategy_version). Any engaged applicable
scope blocks; precedence for the reported reason is GLOBAL > STRATEGY > SYMBOL.

Fail-closed: if state cannot be read (DB error, missing table, corrupt row) the switch is reported
ENGAGED with reason ``kill_switch_unreadable`` — never as released.

Every change is appended to ``ledger_kill_switch_audit`` (hash-chained, append-only). No-op calls
(engage when already engaged, release when already released) write nothing, which makes recovery
idempotent.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import GLOBAL_KEY, KillScope, LedgerKillSwitch, LedgerKillSwitchAudit
from .repository import GENESIS_HASH, canonical_json

_PRECEDENCE = {KillScope.GLOBAL: 0, KillScope.STRATEGY: 1, KillScope.SYMBOL: 2}


class KillSwitchAuditBroken(Exception):
    pass


@dataclass(frozen=True)
class KillSwitchState:
    engaged: bool
    reasons: tuple[str, ...] = ()
    scopes: tuple[tuple[str, str], ...] = ()
    error: str | None = None  # set when fail-closed due to unreadable state

    @property
    def reason(self) -> str:
        return self.reasons[0] if self.reasons else ""


def _norm(scope: KillScope | str, key: str | None) -> tuple[KillScope, str]:
    scope = KillScope(scope)
    if scope is KillScope.GLOBAL:
        return scope, GLOBAL_KEY
    if not (isinstance(key, str) and key.strip()):
        raise ValueError(f"{scope.value} scope requires a key")
    return scope, key


def _audit_hash(prev_hash: str, **fields) -> str:
    return hashlib.sha256((prev_hash + "|" + canonical_json(fields)).encode()).hexdigest()


class KillSwitch:
    def __init__(self, session_factory: Callable[[], Session], clock: Callable[[], datetime]):
        self._sf = session_factory
        self._clock = clock

    def _now(self) -> datetime:
        t = self._clock()
        if t.tzinfo is None:
            raise ValueError("clock must return timezone-aware datetimes")
        return t.astimezone(timezone.utc)

    # ── writes ───────────────────────────────────────────────────────────────

    def _set(self, scope, key, *, engaged: bool, reason: str, actor: str) -> bool:
        scope, key = _norm(scope, key)
        with self._sf() as s, s.begin():
            row = s.execute(
                select(LedgerKillSwitch).where(LedgerKillSwitch.scope == scope.value, LedgerKillSwitch.scope_key == key)
            ).scalar_one_or_none()
            if row is not None and row.engaged is engaged:
                return False  # no-op: nothing written
            if row is None and not engaged:
                return False
            now = self._now()
            if row is None:
                row = LedgerKillSwitch(scope=scope.value, scope_key=key)
                s.add(row)
            row.engaged = engaged
            row.reason = reason
            row.actor = actor
            row.engaged_at = now if engaged else None
            row.updated_at = now
            last = s.execute(
                select(LedgerKillSwitchAudit).order_by(LedgerKillSwitchAudit.seq.desc()).limit(1)
            ).scalar_one_or_none()
            prev = last.entry_hash if last else GENESIS_HASH
            seq = (last.seq if last else 0) + 1
            action = "ENGAGE" if engaged else "RELEASE"
            entry = LedgerKillSwitchAudit(
                seq=seq, scope=scope.value, scope_key=key, action=action, engaged_after=engaged,
                reason=reason, actor=actor, at=now, prev_hash=prev,
            )
            entry.entry_hash = _audit_hash(prev, seq=seq, scope=scope.value, scope_key=key, action=action,
                                           engaged_after=engaged, reason=reason, actor=actor, at=now)
            s.add(entry)
            return True

    def engage(self, scope: KillScope | str, key: str | None = None, *, reason: str, actor: str = "system") -> bool:
        """Engage a scope. Returns True if state changed (audited), False if already engaged."""
        if not (isinstance(reason, str) and reason.strip()):
            raise ValueError("engage requires a reason")
        if not (isinstance(actor, str) and actor.strip()):
            raise ValueError("engage requires an actor")
        return self._set(scope, key, engaged=True, reason=reason, actor=actor)

    def release(self, scope: KillScope | str, key: str | None = None, *, actor: str, reason: str) -> bool:
        """Release a scope. Explicit human actor + reason are mandatory."""
        if not (isinstance(actor, str) and actor.strip()):
            raise ValueError("release requires an explicit actor")
        if not (isinstance(reason, str) and reason.strip()):
            raise ValueError("release requires an explicit reason")
        return self._set(scope, key, engaged=False, reason=reason, actor=actor)

    # ── reads (fail-closed) ──────────────────────────────────────────────────

    def check(self, *, symbol: str | None = None, strategy: str | None = None) -> KillSwitchState:
        wanted = {(KillScope.GLOBAL.value, GLOBAL_KEY)}
        if symbol:
            wanted.add((KillScope.SYMBOL.value, symbol))
        if strategy:
            wanted.add((KillScope.STRATEGY.value, strategy))
        try:
            with self._sf() as s:
                rows = list(s.execute(select(LedgerKillSwitch)).scalars())
                hits = []
                for r in rows:
                    if (r.scope, r.scope_key) not in wanted:
                        continue
                    if r.engaged is not True and r.engaged is not False:
                        raise ValueError(f"corrupt kill switch row {r.scope}/{r.scope_key}: engaged={r.engaged!r}")
                    if r.engaged:
                        hits.append((_PRECEDENCE[KillScope(r.scope)], r.scope, r.scope_key, r.reason))
        except Exception as e:  # noqa: BLE001 — fail closed on ANY read problem
            why = f"kill_switch_unreadable: {type(e).__name__}"
            return KillSwitchState(engaged=True, reasons=(why,), scopes=(), error=why)
        hits.sort()
        return KillSwitchState(
            engaged=bool(hits),
            reasons=tuple(f"{sc}:{k}: {rsn}" for _, sc, k, rsn in hits),
            scopes=tuple((sc, k) for _, sc, k, _ in hits),
        )

    def is_engaged(self, *, symbol: str | None = None, strategy: str | None = None) -> bool:
        return self.check(symbol=symbol, strategy=strategy).engaged

    def audit(self) -> list[LedgerKillSwitchAudit]:
        with self._sf() as s:
            rows = list(s.execute(select(LedgerKillSwitchAudit).order_by(LedgerKillSwitchAudit.seq)).scalars())
            for r in rows:
                s.expunge(r)
            return rows

    def verify_audit(self) -> int:
        prev = GENESIS_HASH
        rows = self.audit()
        for i, r in enumerate(rows, start=1):
            if r.seq != i or r.prev_hash != prev:
                raise KillSwitchAuditBroken(f"audit seq {r.seq}: chain gap")
            h = _audit_hash(prev, seq=r.seq, scope=r.scope, scope_key=r.scope_key, action=r.action,
                            engaged_after=r.engaged_after, reason=r.reason, actor=r.actor, at=r.at)
            if h != r.entry_hash:
                raise KillSwitchAuditBroken(f"audit seq {r.seq}: content altered")
            prev = r.entry_hash
        return len(rows)
