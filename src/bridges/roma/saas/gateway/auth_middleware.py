"""Unified auth middleware — API Key + optional JWT."""

import jwt
import os
from typing import Optional
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

ALGORITHM = "HS256"


class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        api_key_header: str = "X-API-Key",
        jwt_secret: Optional[str] = None,
        jwt_algorithm: str = "HS256",
        jwt_expire_minutes: int = 60,
        require_jwt: bool = False,
        allowed_origins: list[str] = None,
        tenant_config=None,
    ):
        super().__init__(app)
        self.api_key_header = api_key_header.upper().replace("-", "_")
        self.jwt_secret = jwt_secret or os.getenv("JWT_SECRET", "")
        self.jwt_algorithm = jwt_algorithm
        self.jwt_expire_minutes = jwt_expire_minutes
        self.require_jwt = require_jwt
        self.allowed_origins = allowed_origins or ["*"]
        self.tenant_config = tenant_config or {}

    async def dispatch(self, request: Request, call_next):
        from starlette.responses import JSONResponse

        try:
            origin = request.headers.get("origin", "")
            if self._cors_origin_match(origin):
                request.state.origin_allowed = True

            tenant_id = getattr(request.state, "tenant_id", None)

            if tenant_id and tenant_id in self.tenant_config:
                cfg = self.tenant_config[tenant_id]
                auth_cfg = cfg.auth if hasattr(cfg, "auth") else None
            else:
                auth_cfg = None

            if auth_cfg and not auth_cfg.enabled:
                return await call_next(request)

            api_key = self._get_api_key(request)
            jwt_token = self._get_jwt(request)

            # --- Require API key: reject immediately if missing ---
            if auth_cfg and auth_cfg.require_api_key and not api_key:
                return JSONResponse({"detail": "Missing API key"}, status_code=401)

            # --- Validate API key ---
            if api_key:
                request.state.api_key = api_key
                request.state.auth_type = "api_key"
                valid = await self._validate_api_key(api_key, tenant_id)
                if not valid:
                    return JSONResponse({"detail": "Invalid API key"}, status_code=401)
            elif jwt_token:
                request.state.auth_type = "jwt"
                payload = self._decode_jwt(jwt_token)
                if not payload:
                    return JSONResponse({"detail": "Invalid or expired JWT"}, status_code=401)
                request.state.jwt_payload = payload

            response = await call_next(request)
            return response
        except HTTPException:
            raise
        except Exception as e:
            return JSONResponse({"detail": f"Auth error: {str(e)}"}, status_code=401)

    def _get_api_key(self, request: Request) -> Optional[str]:
        for header_name in ["X-API-Key", "X-API-KEY", "Authorization"]:
            if header_name in request.headers:
                val = request.headers[header_name]
                if header_name == "Authorization" and val.startswith("ApiKey "):
                    return val[7:]
                if header_name in ("X-API-Key", "X-API-KEY"):
                    return val
        return None

    def _get_jwt(self, request: Request) -> Optional[str]:
        auth = request.headers.get("authorization", "")
        if auth.startswith("Bearer "):
            return auth[7:]
        return None

    async def _validate_api_key(self, key: str, tenant_id: Optional[str]) -> bool:
        if not key or len(key) < 16:
            return False
        if tenant_id:
            from saas.tenants.manager import TenantManager

            try:
                manager = TenantManager()
                tenant = manager.get_tenant(tenant_id)
                if tenant:
                    stored_key = tenant.get("api_key", "")
                    return stored_key == key
            except Exception:
                pass
        return True

    def _decode_jwt(self, token: str) -> Optional[dict]:
        if not self.jwt_secret:
            return None
        try:
            return jwt.decode(
                token,
                self.jwt_secret,
                algorithms=[self.jwt_algorithm],
            )
        except jwt.ExpiredSignatureError:
            raise HTTPException(401, "JWT expired")
        except jwt.InvalidTokenError:
            raise HTTPException(401, "Invalid JWT")

    def _cors_origin_match(self, origin: str) -> bool:
        if "*" in self.allowed_origins:
            return True
        return origin in self.allowed_origins
