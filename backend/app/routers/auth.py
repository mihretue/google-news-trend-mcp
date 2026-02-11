from fastapi import APIRouter, HTTPException, status
from fastapi.responses import Response
import logging
from typing import Dict, Any

from app.schemas.auth import SignupRequest, LoginRequest, AuthResponse
from app.services.db.supabase_client import supabase_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.options("/signup")
@router.options("/login")
@router.options("/logout")
async def auth_options():
    """Handle CORS preflight requests for auth endpoints."""
    return Response(status_code=200)


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def signup(request: SignupRequest) -> Dict[str, Any]:
    """
    Create a new user account.
    
    - **email**: User email address
    - **password**: User password (minimum 8 characters)
    
    Returns authentication token and user information.
    """
    try:
        # Create user in Supabase
        result = supabase_client.create_user(request.email, request.password)
        
        user = result["user"]
        session = result["session"]
        
        if not session or not session.access_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create user account",
            )
        
        logger.info(f"User signup successful: {request.email}")
        
        return AuthResponse(
            access_token=session.access_token,
            token_type="bearer",
            user_id=user.id,
            email=user.email,
        )
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Signup error: {error_msg}")
        
        # Map specific Supabase errors to user-friendly messages
        if "already registered" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )
        elif "password" in error_msg.lower() and "weak" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password is too weak. Use at least 8 characters with uppercase, lowercase, numbers, and special characters",
            )
        elif "too many requests" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many signup attempts. Please try again later",
            )
        elif "invalid email" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email address",
            )
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg if error_msg else "Failed to create user account",
        )


@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest) -> Dict[str, Any]:
    """
    Authenticate user with email and password.
    
    - **email**: User email address
    - **password**: User password
    
    Returns authentication token and user information.
    """
    try:
        logger.info(f"[LOGIN] Login request received for email: {request.email}")
        
        # Authenticate user
        result = supabase_client.authenticate_user(request.email, request.password)
        
        logger.info(f"[LOGIN] Authentication result received")
        logger.info(f"[LOGIN] Result keys: {result.keys()}")
        
        user = result["user"]
        session = result["session"]
        
        logger.info(f"[LOGIN] User: {user}")
        logger.info(f"[LOGIN] Session: {session}")
        logger.info(f"[LOGIN] Session type: {type(session)}")
        
        if not session:
            logger.error(f"[LOGIN] Session is None for user {request.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
        
        if not session.access_token:
            logger.error(f"[LOGIN] No access_token in session for user {request.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
        
        logger.info(f"[LOGIN] Access token obtained, length: {len(session.access_token)}")
        logger.info(f"[LOGIN] User login successful: {request.email}")
        
        response = AuthResponse(
            access_token=session.access_token,
            token_type="bearer",
            user_id=user.id,
            email=user.email,
        )
        
        logger.info(f"[LOGIN] Returning AuthResponse: {response}")
        
        return response
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        logger.error(f"[LOGIN] Login error: {error_msg}")
        logger.error(f"[LOGIN] Error type: {type(e)}")
        import traceback
        logger.error(f"[LOGIN] Traceback: {traceback.format_exc()}")
        
        # Map specific Supabase errors to user-friendly messages
        if "invalid login credentials" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
        elif "too many requests" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many login attempts. Please try again later",
            )
        elif "email not confirmed" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Email not confirmed. Please check your email",
            )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout() -> Dict[str, str]:
    """
    Logout user (frontend-side token removal).
    
    Note: Token invalidation is handled by the frontend removing the token.
    """
    logger.info("User logout")
    return {"message": "Logged out successfully"}
