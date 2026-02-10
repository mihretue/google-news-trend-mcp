from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
import logging
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

# Public routes that don't require authentication
PUBLIC_ROUTES = {
    "/health",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/auth/signup",
    "/auth/login",
}


class AuthMiddleware:
    """Middleware for JWT token validation and user context injection."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, request: Request, call_next):
        """Process request and validate authentication."""
        # Check if route is public
        if request.url.path in PUBLIC_ROUTES or request.url.path.startswith("/auth/"):
            return await call_next(request)

        # Extract and validate token
        token = self._extract_token(request)
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization required",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Validate token and extract user_id
        user_id = self._validate_token(token)
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Attach user_id to request state
        request.state.user_id = user_id
        request.state.token = token

        return await call_next(request)

    @staticmethod
    def _extract_token(request: Request) -> Optional[str]:
        """Extract JWT token from Authorization header."""
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return None

        try:
            scheme, token = auth_header.split()
            if scheme.lower() != "bearer":
                return None
            return token
        except ValueError:
            return None

    @staticmethod
    def _validate_token(token: str) -> Optional[str]:
        """Validate JWT token and extract user_id."""
        try:
            payload = jwt.decode(
                token,
                settings.supabase_jwt_secret,
                algorithms=["HS256"],
            )
            user_id = payload.get("sub")
            if not user_id:
                logger.warning("Token missing 'sub' claim")
                return None
            return user_id
        except JWTError as e:
            logger.warning(f"Token validation failed: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during token validation: {str(e)}")
            return None


def get_user_id(request: Request) -> str:
    """Get user_id from request state."""
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not authenticated",
        )
    return user_id
