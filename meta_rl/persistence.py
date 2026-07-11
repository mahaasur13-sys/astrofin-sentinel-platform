"""meta_rl/persistence.py — ATOM-META-RL-007/009/012/013: Full Persistence"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

DATA = Path(__file__).parent.parent / "data" / "meta_rl"
VERSIONS = DATA / "versions"
SESSIONS = DATA / "sessions"
SESSIONS.mkdir(parents=True, exist_ok=True)
VERSIONS.mkdir(parents=True, exist_ok=True)


def dj(obj):
    return json.dumps(obj, default=str, ensure_ascii=False)


def dl(text):
    try:
        return json.loads(text) if text else []
    except Exception:  # noqa: BLE001
        return []


def ld(text):
    try:
        return json.loads(text) if text else {}
    except Exception:  # noqa: BLE001
        return {}


class MetaRLPersistence:
    """
    Full persistence layer for meta_rl.

    Storage layout:
        data/meta_rl/sessions/<session_id>_meta.json       — session metadata
        data/meta_rl/sessions/<session_id>_strategies.json — scored strategies
        data/meta_rl/sessions/<session_id>_evolution.json   — evolution session state
        data/meta_rl/versions/v_<tag>/strategies.json       — frozen version

    Also integrates with core/history_db for sentinel run sessions.
    """

    enabled = True

    # ── ScoredStrategy persistence ─────────────────────────────────────────────

    def save_scored_strategy(self, scored, session_id: str) -> bool:
        """Append a ScoredStrategy record to the session's strategies file."""
        try:
            path = SESSIONS / f"{session_id}_strategies.json"
            records = dl(path.read_text()) if path.exists() else []

            ev = getattr(scored, "evaluation", None)
            strat = getattr(scored, "strategy", None)
            strat_dict = (
                strat.to_dict()
                if hasattr(strat, "to_dict")
                else {
                    "chromosome": getattr(strat, "chromosome", {}),
                    "generation": getattr(scored, "generation", 1),
                    "parent_fitness": 0.0,
                    "config": {},
                }
            )

            records.append(
                {
                    "id": getattr(scored, "id", ""),
                    "session_id": session_id,
                    "generation": getattr(scored, "generation", 1),
                    "parent_ids": list(getattr(scored, "parent_ids", [])),
                    "reward": float(getattr(scored, "reward", 0.0)),
                    "reward_history": list(getattr(scored, "reward_history", [])),
                    "risk_adjusted_pnl": getattr(ev, "risk_adjusted_pnl", 0.0) if ev else 0.0,
                    "sharpe": getattr(ev, "sharpe", 0.0) if ev else 0.0,
                    "max_drawdown": getattr(ev, "max_drawdown", 1.0) if ev else 1.0,
                    "trades": getattr(ev, "trades", 0) if ev else 0,
                    "win_rate": getattr(ev, "win_rate", 0.0) if ev else 0.0,
                    "chromosome": strat_dict.get("chromosome", {}),
                    "metadata": getattr(scored, "metadata", {}),
                    "saved_at": datetime.now(timezone.utc).isoformat(),
                }
            )

            path.write_text(dj(records), encoding="utf-8")
            logger.debug(f"[META-RL-PERSIST] Saved strategy {scored.id[:8]} → {path.name}")
            return True
        except Exception as e:  # noqa: BLE001
            logger.warning(f"[META-RL-PERSIST] save_scored_strategy failed: {e}")
            return False

    def load_scored_strategies(self, session_id: str) -> list[dict[str, Any]]:
        """Load all scored strategy records for a session."""
        path = SESSIONS / f"{session_id}_strategies.json"
        if not path.exists():
            return []
        try:
            return dl(path.read_text())
        except Exception as e:  # noqa: BLE001
            logger.warning(f"[META-RL-PERSIST] load_scored_strategies({session_id}) failed: {e}")
            return []

    def save_session_metadata(self, session_id: str, metadata: dict[str, Any]) -> bool:
        """Save arbitrary metadata for a session."""
        try:
            path = SESSIONS / f"{session_id}_meta.json"
            record = {
                "session_id": session_id,
                "saved_at": datetime.now(timezone.utc).isoformat(),
                **metadata,
            }
            path.write_text(dj(record), encoding="utf-8")
            return True
        except Exception as e:  # noqa: BLE001
            logger.warning(f"[META-RL-PERSIST] save_session_metadata failed: {e}")
            return False

    def load_session_metadata(self, session_id: str) -> dict[str, Any] | None:
        """Load session metadata, returns None if not found."""
        path = SESSIONS / f"{session_id}_meta.json"
        if not path.exists():
            return None
        try:
            return ld(path.read_text())
        except Exception:  # noqa: BLE001
            return None

    def list_sessions(self) -> list[str]:
        """List all known meta_rl session IDs (JSON files + sentinel history_db)."""
        session_ids = set()

        # meta_rl native sessions
        try:
            for f in SESSIONS.iterdir():
                if f.name.endswith("_strategies.json") or f.name.endswith("_meta.json"):
                    sid = f.name.replace("_strategies.json", "").replace("_meta.json", "")
                    session_ids.add(sid)
        except Exception as e:  # noqa: BLE001
            logger.warning(f"[META-RL-PERSIST] list_sessions scan failed: {e}")

        # sentinel sessions from core/history_db
        try:
            from core.history_db import list_sessions as db_list_sessions

            for row in db_list_sessions(limit=1000):
                sid = str(row.get("session_id", ""))
                if sid:
                    session_ids.add(sid)
        except Exception as e:  # noqa: BLE001
            logger.debug(f"[META-RL-PERSIST] core/history_db not available: {e}")

        return sorted(session_ids)

    # ── Elite chromosomes ───────────────────────────────────────────────────────

    def save_elite_chromosomes(self, scored_strategies, session_id: str) -> int:
        """Save elite chromosomes (batch of save_scored_strategy)."""
        if not scored_strategies:
            return 0
        count = sum(1 for s in scored_strategies if self.save_scored_strategy(s, session_id))
        logger.info(f"[META-RL-PERSIST] Saved {count} elite chromosomes → {session_id}")
        return count

    def load_elite_chromosomes(self, session_id: str) -> list[dict[str, Any]]:
        """Alias for load_scored_strategies."""
        return self.load_scored_strategies(session_id)

    # ── Evolution session (ATOM-META-RL-013) ───────────────────────────────────

    def save_evolution_session(
        self,
        session_id: str,
        symbol: str,
        cg: int,
        br: float,
        ks: dict,
        gs: list,
    ) -> bool:
        """Save full evolution session state (called from EvolutionEngine._save_generation)."""
        if not self.enabled:
            return False
        try:
            path = SESSIONS / f"{session_id}_evolution.json"
            data = {
                "session_id": session_id,
                "symbol": symbol,
                "current_generation": cg,
                "best_reward": float(br),
                "karl_state": dict(ks),
                "history": [s.to_dict() if hasattr(s, "to_dict") else s for s in gs],
                "saved_at": datetime.now(timezone.utc).isoformat(),
            }
            path.write_text(dj(data), encoding="utf-8")
            logger.debug(f"[META-RL-PERSIST] Saved evolution session: {session_id}")
            return True
        except Exception as e:  # noqa: BLE001
            logger.warning(f"[META-RL-PERSIST] save_evolution_session failed: {e}")
            return False

    def load_evolution_session(self, session_id: str) -> dict | None:
        """Load evolution session state (called from EvolutionEngine._load_session)."""
        try:
            path = SESSIONS / f"{session_id}_evolution.json"
            if not path.exists():
                return None
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:  # noqa: BLE001
            logger.warning(f"[META-RL-PERSIST] load_evolution_session failed: {e}")
            return None

    # ── Version management ───────────────────────────────────────────────────────

    def save_version(self, strategies: list[Any], version_tag: str) -> bool:
        """Save a frozen generation of strategies as a named version."""
        if not self.enabled:
            return False
        tag = str(version_tag).replace(" ", "_").replace("/", "_").replace(":", "-")
        ver_dir = VERSIONS / f"v_{tag}"
        ver_dir.mkdir(exist_ok=True)

        records = []
        for s in strategies or []:
            ev = getattr(s, "evaluation", None)
            strat = getattr(s, "strategy", None)
            strat_dict = (
                strat.to_dict()
                if hasattr(strat, "to_dict")
                else {
                    "chromosome": getattr(strat, "chromosome", {}),
                    "generation": getattr(s, "generation", 0),
                    "parent_fitness": 0.0,
                    "config": {},
                }
            )
            records.append(
                {
                    "id": getattr(s, "id", ""),
                    "generation": getattr(s, "generation", 0),
                    "reward": getattr(s, "reward", 0.0),
                    "risk_adjusted_pnl": getattr(ev, "risk_adjusted_pnl", 0.0) if ev else 0.0,
                    "sharpe": getattr(ev, "sharpe", 0.0) if ev else 0.0,
                    "max_drawdown": getattr(ev, "max_drawdown", 1.0) if ev else 1.0,
                    "trades": getattr(ev, "trades", 0) if ev else 0,
                    "chromosome": strat_dict.get("chromosome", {}),
                }
            )

        (ver_dir / "strategies.json").write_text(dj(records), encoding="utf-8")

        idx_path = VERSIONS / "versions_index.json"
        try:
            index = ld(idx_path.read_text()) if idx_path.exists() else {}
        except Exception:  # noqa: BLE001
            index = {}
        idx_data = index.get("versions", [])
        if tag not in idx_data:
            idx_data.append(tag)
            index["versions"] = idx_data
            idx_path.write_text(dj(index), encoding="utf-8")

        logger.info(f"[META-RL-PERSIST] Version {tag}: {len(records)} strategies saved")
        return True

    def load_version(self, version_tag: str) -> list[dict[str, Any]]:
        """Load a frozen version by tag."""
        tag = str(version_tag).replace(" ", "_").replace("/", "_").replace(":", "-")
        path = VERSIONS / f"v_{tag}" / "strategies.json"
        if not path.exists():
            return []
        try:
            return dl(path.read_text())
        except Exception as e:  # noqa: BLE001
            logger.warning(f"[META-RL-PERSIST] load_version({tag}) failed: {e}")
            return []

    def list_versions(self) -> list[str]:
        """List all available version tags."""
        idx = VERSIONS / "versions_index.json"
        try:
            if idx.exists():
                index = ld(idx.read_text())
                return index.get("versions", [])
        except Exception:  # noqa: BLE001
            pass
        return []

    def compare_versions(self, va: str, vb: str) -> dict[str, Any]:
        """Compare two versions by mean reward."""
        da = self.load_version(va)
        db = self.load_version(vb)
        if not da or not db:
            return {"error": "version not found", "a": va, "b": vb}
        try:
            import numpy as np

            ra = [float(x.get("reward", 0.0)) for x in da]
            rb = [float(x.get("reward", 0.0)) for x in db]
            ma = float(np.mean(ra)) if ra else 0.0
            mb = float(np.mean(rb)) if rb else 0.0
            return {
                "a": va,
                "b": vb,
                "a_mean": round(ma, 4),
                "b_mean": round(mb, 4),
                "a_count": len(ra),
                "b_count": len(rb),
                "winner": va if ma > mb else vb,
            }
        except Exception as exc:  # noqa: BLE001
            return {"error": str(exc), "a": va, "b": vb}

    # ── Cross-session summary ────────────────────────────────────────────────────

    def get_sessions_summary(self) -> dict[str, Any]:
        """Return aggregated stats across all meta_rl sessions."""
        try:
            sessions = self.list_sessions()
            total_strategies = 0
            all_rewards: list[float] = []
            gen_counts: dict[int, int] = {}

            for sid in sessions:
                records = self.load_scored_strategies(sid)
                total_strategies += len(records)
                for r in records:
                    all_rewards.append(float(r.get("reward", 0.0)))
                    gen = int(r.get("generation", 0))
                    gen_counts[gen] = gen_counts.get(gen, 0) + 1

            import numpy as np

            mean_r = float(np.mean(all_rewards)) if all_rewards else 0.0
            max_r = float(np.max(all_rewards)) if all_rewards else 0.0

            return {
                "total_sessions": len(sessions),
                "total_strategies": total_strategies,
                "mean_reward": round(mean_r, 4),
                "max_reward": round(max_r, 4),
                "generations_distribution": gen_counts,
                "versions": self.list_versions(),
            }
        except Exception as e:  # noqa: BLE001
            logger.warning(f"[META-RL-PERSIST] get_sessions_summary failed: {e}")
            return {
                "total_sessions": 0,
                "total_strategies": 0,
                "mean_reward": 0.0,
                "max_reward": 0.0,
                "generations_distribution": {},
                "versions": [],
            }


_persistence: MetaRLPersistence | None = None


def get_persistence() -> MetaRLPersistence:
    global _persistence
    if _persistence is None:
        _persistence = MetaRLPersistence()
    return _persistence
