"""Jev (TypeSafe AI "System One" decision model) client via OpenRouter Decisions API.

Jev is **not** a chat model. It consumes a JSON ``state`` and a map of typed
``questions`` and returns one typed decision per question (``noul`` / ``choice`` /
``score``) with calibrated probabilities — no prose, no chain-of-thought.

Wire format (beta)::

    POST {base_url}/decisions
    { "model": "typesafe/jev-1.13", "state": <str|obj|list>, "questions": { name: {...} } }

Pinned model: ``typesafe/jev-1.13``. ``typesafe/jev-latest`` is **forbidden**.

Fail-closed contract — any violation raises :class:`JevError`, never a default
"allow":
    * non-2xx, redirect (3xx), timeout, transport error
    * non-JSON body or invalid response schema
    * input exceeding the 32K-token budget (state + questions; never truncated)
    * base_url host outside the allowlist (``openrouter.ai`` + loopback for tests)
    * model not pinned to ``typesafe/jev-1.13``

The key is the existing ``OPENROUTER_API_KEY`` (surfaced as
``core.settings.Settings.jev_api_key``); it is never logged and never present
in this file. Retries are idempotent by content (identical body every attempt).
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

import httpx

from core.http_client import get_http_client
from core.settings import settings

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────
PINNED_JEV_MODEL = "typesafe/jev-1.13"
FORBIDDEN_MODEL_MARKERS = ("jev-latest",)
# 32K-token budget on state+questions. Tokens are approximated as
# len(text) // CHARS_PER_TOKEN (conservative: it under-counts tokens, so the
# guard trips *before* a real overflow rather than after).
TOKEN_BUDGET = 32_000
CHARS_PER_TOKEN = 4
ALLOWED_HOSTS = frozenset({"openrouter.ai", "127.0.0.1", "localhost"})
MAX_RETRIES = 2


class JevError(RuntimeError):
    """Base failure for the Jev client. Callers MUST treat this as escalation."""

    def __init__(self, message: str, *, status: int | None = None, reason: str = ""):
        super().__init__(message)
        self.status = status
        self.reason = reason


@dataclass(frozen=True)
class JevAnswer:
    """One typed decision.

    ``value`` semantics depend on the question type:
        * ``noul``   → float ``P(true)`` in [0, 1]
        * ``choice`` → selected key (str) out of the question ``criteria``
        * ``score``  → float expected value (may be fractional)
    """

    type: str
    value: Any
    probabilities: dict[str, float] | list[float] | None = None
    confidence: float | None = None


@dataclass(frozen=True)
class JevUsage:
    """Token/cost accounting for one decision call (recorded in the call log)."""

    input_tokens: int = 0
    output_tokens: int = 0
    cost: float = 0.0
    provider: str = "openrouter"


@dataclass(frozen=True)
class JevDecisions:
    """Typed result of a :meth:`JevClient.decide` call."""

    model: str
    answers: dict[str, JevAnswer]
    usage: JevUsage


# ── Helpers ─────────────────────────────────────────────────────────────


def _get(d: dict, *names: str) -> Any:
    """Permissive field fetch (the beta endpoint is tolerant to field naming)."""
    for name in names:
        if name in d and d[name] is not None:
            return d[name]
    return None


def _as_int(v: Any) -> int:
    try:
        return int(v or 0)
    except (TypeError, ValueError):
        return 0


def _as_float(v: Any) -> float:
    if isinstance(v, bool):
        return 1.0 if v else 0.0
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def _as_float_opt(v: Any) -> float | None:
    if v is None:
        return None
    if isinstance(v, bool):
        return 1.0 if v else 0.0
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _parse_answer(name: str, raw: Any) -> JevAnswer:
    """Parse one answer, permissively on field names but fail-closed on absence."""
    if not isinstance(raw, dict):
        raise JevError(f"Jev answer {name!r} is not an object", reason="invalid_schema")

    noul = _get(raw, "noul", "probability", "p")
    choice = _get(raw, "choice")
    score = _get(raw, "score")
    probabilities = _get(raw, "probabilities", "distribution")
    confidence = _get(raw, "confidence")

    if noul is not None:
        value = 1.0 if noul is True else (0.0 if noul is False else _as_float(noul))
        conf = _as_float_opt(confidence)
        if conf is None:  # for noul, probability IS the confidence when absent
            conf = value
        return JevAnswer(type="noul", value=value, probabilities=probabilities, confidence=conf)

    if choice is not None:
        return JevAnswer(
            type="choice",
            value=str(choice),
            probabilities=probabilities,
            confidence=_as_float_opt(confidence),
        )

    if score is not None:
        return JevAnswer(
            type="score",
            value=_as_float(score),
            probabilities=probabilities,
            confidence=_as_float_opt(confidence),
        )

    raise JevError(
        f"Jev answer {name!r} has no parseable value (noul/choice/score)", reason="invalid_schema"
    )


# ── Client ──────────────────────────────────────────────────────────────


class JevClient:
    """Thin async client for OpenRouter's Jev Decisions API (fail-closed)."""

    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        api_key: str,
        timeout: float = 10.0,
        max_retries: int = MAX_RETRIES,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self._client = client
        self._validate()

    # -- fail-closed validation -----------------------------------------
    def _validate(self) -> None:
        host = (urlparse(self.base_url).hostname or "").lower()
        if host not in ALLOWED_HOSTS:
            raise JevError(
                f"Jev base_url host {host!r} not in allowlist {sorted(ALLOWED_HOSTS)}",
                reason="host_deny",
            )
        if self.model != PINNED_JEV_MODEL or any(m in self.model for m in FORBIDDEN_MODEL_MARKERS):
            raise JevError(
                f"Jev model must be pinned to {PINNED_JEV_MODEL!r}, got {self.model!r}",
                reason="model_pin",
            )
        if not self.api_key:
            raise JevError("OPENROUTER_API_KEY is not set", reason="no_key")

    @property
    def url(self) -> str:
        return f"{self.base_url}/decisions"

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    # -- budget guard ----------------------------------------------------
    def _check_budget(self, state: Any, questions: dict) -> None:
        text = json.dumps({"state": state, "questions": questions}, default=str)
        est_tokens = len(text) // CHARS_PER_TOKEN
        if est_tokens > TOKEN_BUDGET:
            raise JevError(
                f"Jev input exceeds {TOKEN_BUDGET}-token budget (est ~{est_tokens} tokens); "
                "refusing to silently truncate",
                reason="budget_overflow",
            )

    # -- decide ----------------------------------------------------------
    async def decide(
        self, state: Any, questions: dict[str, dict], *, timeout: float | None = None
    ) -> JevDecisions:
        """Submit ``state`` + typed ``questions`` and return typed decisions.

        Fail-closed: any non-2xx, redirect, timeout, invalid schema, budget
        overflow, foreign host or unpinned model raises :class:`JevError`.
        Retries (≤2) are idempotent by content — the request body is identical
        on every attempt.
        """
        self._check_budget(state, questions)
        body = {"model": self.model, "state": state, "questions": questions}
        payload = json.dumps(body, default=str)
        t = timeout if timeout is not None else self.timeout
        client = self._client if self._client is not None else get_http_client()

        last_error: JevError | None = None
        for attempt in range(self.max_retries + 1):
            try:
                resp = await client.post(self.url, content=payload, headers=self._headers(), timeout=t)
            except httpx.TimeoutException as exc:
                last_error = JevError(f"Jev request timed out after {t}s", reason="timeout")
                if attempt < self.max_retries:
                    await asyncio.sleep(0.25 * (attempt + 1))
                    continue
                raise last_error from exc
            except httpx.HTTPError as exc:
                raise JevError(
                    f"Jev transport error: {type(exc).__name__}: {exc}", reason="transport"
                ) from exc

            # Redirect → fail-closed (credentials/metadata must not leak to another host).
            if 300 <= resp.status_code < 400:
                raise JevError(
                    f"Jev redirect rejected (status {resp.status_code}, "
                    f"Location={resp.headers.get('location', '?')})",
                    status=resp.status_code,
                    reason="redirect",
                )

            # Idempotent retry only on 429 / 5xx.
            if (resp.status_code == 429 or resp.status_code >= 500) and attempt < self.max_retries:
                last_error = JevError(
                    f"Jev HTTP {resp.status_code}", status=resp.status_code, reason="retryable_http"
                )
                await asyncio.sleep(0.25 * (attempt + 1))
                continue

            if resp.status_code >= 400:
                raise JevError(
                    f"Jev HTTP {resp.status_code}: {resp.text[:300]}",
                    status=resp.status_code,
                    reason="http",
                )

            return self._parse(resp)

        raise last_error or JevError("Jev retries exhausted", reason="retry")

    # -- response parsing -------------------------------------------------
    def _parse(self, resp: httpx.Response) -> JevDecisions:
        try:
            data = resp.json()
        except Exception as exc:  # noqa: BLE001 — non-JSON body (proxy/Cloudflare page)
            raise JevError("Jev response is not valid JSON", reason="invalid_json") from exc

        if not isinstance(data, dict):
            raise JevError("Jev response must be a JSON object", reason="invalid_schema")

        answers_raw = data.get("answers")
        if not isinstance(answers_raw, dict) or not answers_raw:
            raise JevError("Jev response missing/invalid 'answers'", reason="invalid_schema")

        answers: dict[str, JevAnswer] = {}
        for name, raw in answers_raw.items():
            answers[name] = _parse_answer(name, raw)

        usage_raw = data.get("usage") if isinstance(data.get("usage"), dict) else {}
        usage = JevUsage(
            input_tokens=_as_int(usage_raw.get("input_tokens")),
            output_tokens=_as_int(usage_raw.get("output_tokens")),
            cost=_as_float(usage_raw.get("cost")),
            provider="openrouter",
        )

        decisions = JevDecisions(model=str(data.get("model") or self.model), answers=answers, usage=usage)
        self._log(decisions)
        return decisions

    def _log(self, decisions: JevDecisions) -> None:
        # Never log the state/questions (PII) — only accounting + model echo.
        logger.info(
            "jev decide: model=%s answers=%d input_tokens=%d output_tokens=%d cost=%.8f provider=%s",
            decisions.model,
            len(decisions.answers),
            decisions.usage.input_tokens,
            decisions.usage.output_tokens,
            decisions.usage.cost,
            decisions.usage.provider,
        )


# ── Lazy singleton ──────────────────────────────────────────────────────
_JEV_CLIENT: JevClient | None = None


def get_jev_client() -> JevClient:
    """Return the process-wide :class:`JevClient` singleton (config from ``core.settings``)."""
    global _JEV_CLIENT
    if _JEV_CLIENT is None:
        _JEV_CLIENT = JevClient(
            base_url=settings.jev_base_url,
            model=settings.jev_model,
            api_key=settings.jev_api_key.get_secret_value(),
            timeout=settings.jev_timeout_s,
        )
    return _JEV_CLIENT
