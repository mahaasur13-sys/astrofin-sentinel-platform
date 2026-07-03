"""Role-based access policy for FastAPI endpoints (P1-13).

Two roles are supported:

  - ``reader`` — read-only access (default for new users)
  - ``admin``  — full access, including secret rotation and audit
                 inspection

A user's role is stored in the JWT payload under the ``role`` claim
and is set at login time from the ``dev_users`` table in
``config/secrets.yaml``. The role check uses :func:`fastapi_require_role`
as a FastAPI dependency:

.. code-block:: python

    from core.access_policy import fastapi_require_role

    @router.post("/secrets/rotate", dependencies=[Depends(fasti_require_role("admin"))])
    def rotate_secret(...): ...

If the role does not match, the endpoint returns 403 and an audit
record is written with status="denied".
"""

from __future__ import annotations

from typing import Iterable, Optional

from fastapi import Depends, HTTPException, Request, status

from core.audit import write_audit

VALID_ROLES = {"admin", "reader"}


def normalize_role(role: Optional[str]) -> str:
    """Map unknown / missing roles to ``reader`` (least privilege)."""
    if not role:
        return "reader"
    role = str(role).strip().lower()
    return role if role in VALID_ROLES else "reader"


def fastapi_require_role(*allowed: str):
    """Build a FastAPI dependency that admits only the listed roles.

    The dependency extracts the JWT payload from the request via the
    standard ``fastapi_require_jwt`` dependency (imported lazily to avoid
    a circular import between ``web.api.auth`` and this module).

    On success the payload is returned; on failure a 403 is raised and an
    ``access.denied`` audit record is appended.
    """
    allowed_set = frozenset(r.strip().lower() for r in allowed)

    async def _dep(request: Request) -> dict:
        from web.api.auth import fastapi_require_jwt  # lazy import

        payload = fastapi_require_jwt(request)
        actor = payload.get("sub", "-")
        role = normalize_role(payload.get("role"))
        if role not in allowed_set:
            write_audit(
                "access.denied",
                actor=actor,
                ip=request.client.host if request.client else "-",
                method=request.method,
                path=request.url.path,
                status="denied",
                detail={"required": sorted(allowed_set), "actual": role},
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role}' not in {sorted(allowed_set)}",
            )
        return payload

    return _dep


__all__ = ["VALID_ROLES", "normalize_role", "fastapi_require_role"]
