"""FastAPI-native auth dependency — runs AFTER middleware chain completes."""

from fastapi import Request, HTTPException, Depends


class AuthContext:
    """Auth info populated by middleware and readable via Depends()."""

    def __init__(self, tenant_id: str = None, api_key: str = None, auth_type: str = None, jwt_payload: dict = None):
        self.tenant_id = tenant_id
        self.api_key = api_key
        self.auth_type = auth_type
        self.jwt_payload = jwt_payload


async def get_auth_context(request: Request) -> AuthContext:
    """
    FastAPI dependency — reads auth state set by AuthMiddleware.
    Runs after full middleware chain, so request.state is complete.
    """
    return AuthContext(
        tenant_id=getattr(request.state, "tenant_id", None),
        api_key=getattr(request.state, "api_key", None),
        auth_type=getattr(request.state, "auth_type", None),
        jwt_payload=getattr(request.state, "jwt_payload", None),
    )


async def require_auth(
    request: Request,
    ctx: AuthContext = Depends(get_auth_context),
) -> AuthContext:
    """
    Require authentication: raises 401 if no valid auth found.
    Use this as a Depends() on protected routes.
    """
    if not ctx.api_key and not ctx.jwt_payload:
        raise HTTPException(401, "Authentication required")
    return ctx
