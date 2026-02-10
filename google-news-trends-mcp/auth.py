"""Authentication and authorization utilities."""

import os
import logging
from typing import Optional
from jose import JWTError, jwt

logger = logging.getLogger(__name__)


class UnauthorizedError(Exception):
    """Raised when authorization fails."""
    pass


def check_authorization(headers) -> str:
    """
    Validate authorization header and extract user_id.
    
    Args:
        headers: Request headers dict
        
    Returns:
        user_id from the JWT token
        
    Raises:
        UnauthorizedError: If authorization is invalid or missing
    """
    auth = headers.get("authorization")
    if not auth or not auth.lower().startswith("bearer "):
        raise UnauthorizedError("Authorization header missing or invalid")
    
    try:
        token = auth.split(" ", 1)[1]
        user_id = validate_token(token)
        if not user_id:
            raise UnauthorizedError("Invalid token")
        return user_id
    except Exception as e:
        logger.warning(f"Authorization check failed: {str(e)}")
        raise UnauthorizedError("Invalid authorization token")


def validate_token(token: str) -> Optional[str]:
    """
    Validate JWT token and extract user_id.
    
    Args:
        token: JWT token string
        
    Returns:
        user_id from token 'sub' claim, or None if invalid
    """
    try:
        jwt_secret = os.getenv("SUPABASE_JWT_SECRET")
        if not jwt_secret:
            logger.warning("SUPABASE_JWT_SECRET not configured")
            return None
        
        payload = jwt.decode(
            token,
            jwt_secret,
            algorithms=["HS256"],
        )
        user_id = payload.get("sub")
        if not user_id:
            logger.warning("Token missing 'sub' claim")
            return None
        return user_id
    except JWTError as e:
        logger.warning(f"JWT validation failed: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error during token validation: {str(e)}")
        return None
