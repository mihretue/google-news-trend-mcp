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
        result = await supabase_client.create_user(request.email, request.password)
        
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
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Signup error: {error_msg}")
        
        # Check for specific error messages
        if "already registered" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create user account",
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
        # Authenticate user
        result = await supabase_client.authenticate_user(request.email, request.password)
        
        user = result["user"]
        session = result["session"]
        
        if not session or not session.access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
        
        logger.info(f"User login successful: {request.email}")
        
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
        logger.error(f"Login error: {error_msg}")
        
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
