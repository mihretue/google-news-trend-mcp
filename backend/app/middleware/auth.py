from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from jose import JWTError, jwt
import logging
from typing import Optional
import httpx

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

# Cache for Supabase public keys
_public_keys_cache = {}


class AuthMiddleware:
    """Middleware for JWT token validation and user context injection."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        """Process request and validate authentication."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive)
        
        logger.info(f"=== MIDDLEWARE CHECK: {request.method} {request.url.path} ===")
        
        # Allow CORS preflight requests to pass through
        if request.method == "OPTIONS":
            logger.info("OPTIONS request, passing through")
            await self.app(scope, receive, send)
            return
        
        # Check if route is public
        if request.url.path in PUBLIC_ROUTES or request.url.path.startswith("/auth/"):
            logger.info(f"Public route: {request.url.path}, passing through")
            await self.app(scope, receive, send)
            return

        logger.info(f"Protected route: {request.url.path}, validating token...")
        
        # Extract and validate token
        token = self._extract_token(request)
        if not token:
            logger.warning(f"No token found for {request.url.path}")
            response = JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Authorization required"},
                headers={"WWW-Authenticate": "Bearer"},
            )
            await response(scope, receive, send)
            return

        logger.info(f"Token extracted, validating...")
        
        # Validate token and extract user_id
        user_id = await self._validate_token(token)
        if not user_id:
            logger.warning(f"Token validation failed for {request.url.path}")
            response = JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid authorization token"},
                headers={"WWW-Authenticate": "Bearer"},
            )
            await response(scope, receive, send)
            return

        logger.info(f"Token validated successfully, user_id: {user_id}")
        
        # Attach user_id to request state
        scope["user_id"] = user_id
        scope["token"] = token

        logger.info(f"Proceeding to next middleware/handler")
        await self.app(scope, receive, send)

    @staticmethod
    def _extract_token(request: Request) -> Optional[str]:
        """Extract JWT token from Authorization header."""
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            logger.debug(f"No Authorization header for {request.url.path}")
            return None

        try:
            scheme, token = auth_header.split()
            if scheme.lower() != "bearer":
                logger.debug(f"Invalid auth scheme: {scheme}")
                return None
            logger.debug(f"Token extracted for {request.url.path}")
            return token
        except ValueError:
            logger.debug("Invalid Authorization header format")
            return None

    @staticmethod
    async def _validate_token(token: str) -> Optional[str]:
        """Validate JWT token and extract user_id."""
        try:
            logger.info("=== TOKEN VALIDATION START ===")
            logger.info(f"Token (first 50 chars): {token[:50]}...")
            
            # First, decode without verification to get the header
            unverified = jwt.get_unverified_header(token)
            logger.info(f"Token header: {unverified}")
            
            # Get the key ID from the token header
            kid = unverified.get("kid")
            logger.info(f"Key ID (kid) from token: {kid}")
            
            if not kid:
                logger.error("Token missing 'kid' in header")
                return None
            
            # Get Supabase public keys
            logger.info(f"Checking cache for kid: {kid}")
            logger.info(f"Current cache keys: {list(_public_keys_cache.keys())}")
            
            if kid not in _public_keys_cache:
                logger.info(f"Kid not in cache, fetching from Supabase...")
                try:
                    async with httpx.AsyncClient() as client:
                        # Use the correct Supabase JWKS endpoint with API key
                        jwks_url = f"{settings.supabase_url}/auth/v1/.well-known/jwks.json"
                        logger.info(f"JWKS URL: {jwks_url}")
                        logger.info(f"Using API key (first 20 chars): {settings.supabase_key[:20]}...")
                        
                        response = await client.get(
                            jwks_url,
                            headers={"apikey": settings.supabase_key},
                            timeout=10
                        )
                        logger.info(f"JWKS response status: {response.status_code}")
                        
                        if response.status_code != 200:
                            logger.error(f"Failed to fetch JWKS: {response.status_code}")
                            logger.error(f"Response text: {response.text}")
                            return None
                        
                        jwks = response.json()
                        available_kids = [k['kid'] for k in jwks.get('keys', [])]
                        logger.info(f"JWKS keys available: {available_kids}")
                        
                        for key in jwks.get("keys", []):
                            _public_keys_cache[key["kid"]] = key
                            logger.info(f"Cached key: {key['kid']}")
                            
                except Exception as e:
                    logger.error(f"Error fetching JWKS: {str(e)}")
                    import traceback
                    logger.error(traceback.format_exc())
                    return None
            else:
                logger.info(f"Kid found in cache!")
            
            if kid not in _public_keys_cache:
                logger.error(f"Public key not found for kid: {kid}")
                logger.error(f"Available keys in cache: {list(_public_keys_cache.keys())}")
                return None
            
            logger.info(f"Using cached public key for kid: {kid}")
            
            # Get the public key
            public_key_data = _public_keys_cache[kid]
            
            # Construct the public key from JWK
            from cryptography.hazmat.primitives.asymmetric import ec
            from cryptography.hazmat.backends import default_backend
            import base64
            import json
            
            logger.info("Reconstructing public key from JWK...")
            
            # For ES256, we need to reconstruct the public key from x and y coordinates
            x = base64.urlsafe_b64decode(public_key_data["x"] + "==")
            y = base64.urlsafe_b64decode(public_key_data["y"] + "==")
            
            # Create the public key
            x_int = int.from_bytes(x, byteorder='big')
            y_int = int.from_bytes(y, byteorder='big')
            
            public_numbers = ec.EllipticCurvePublicNumbers(x_int, y_int, ec.SECP256R1())
            public_key = public_numbers.public_key(default_backend())
            
            logger.info("Public key reconstructed successfully")
            logger.info("Verifying and decoding token...")
            
            # Verify and decode the token
            payload = jwt.decode(
                token,
                public_key,
                algorithms=["ES256"],
                options={"verify_aud": False}
            )
            
            logger.info(f"Token payload: {payload}")
            
            user_id = payload.get("sub")
            if not user_id:
                logger.warning("Token missing 'sub' claim")
                return None
            
            logger.info(f"Token validated successfully for user: {user_id}")
            logger.info("=== TOKEN VALIDATION SUCCESS ===")
            return user_id
            
        except JWTError as e:
            logger.error(f"JWT Error during token validation: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None
        except Exception as e:
            logger.error(f"Unexpected error during token validation: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None


def get_user_id(request: Request) -> str:
    """Get user_id from request state."""
    # Try to get from request.state first (set by middleware)
    user_id = getattr(request.state, "user_id", None)
    if user_id:
        logger.info(f"User ID from request.state: {user_id}")
        return user_id
    
    # Try to get from scope (ASGI level)
    user_id = request.scope.get("user_id")
    if user_id:
        logger.info(f"User ID from scope: {user_id}")
        return user_id
    
    logger.error("User not authenticated - no user_id found")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="User not authenticated",
    )
