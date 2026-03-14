"""
Authentication dependencies for FastAPI routes
Validates Supabase JWT tokens and extracts user information
"""
from fastapi import HTTPException, Header, Depends
from backend.core.supabase_client import supabase
from typing import Optional

async def get_current_user(authorization: str = Header(None)):
    """
    Extract and verify user from Authorization header
    Dependency for protected routes
    """
    if not authorization:
        raise HTTPException(
            status_code=401, 
            detail="Not authenticated. Missing Authorization header."
        )
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header format. Expected 'Bearer <token>'"
        )
    
    token = authorization.split(" ")[1]
    
    try:
        # Verify the JWT token with Supabase
        user_response = supabase.auth.get_user(token)
        
        if not user_response or not user_response.user:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        
        user = user_response.user
        
        return {
            "user_id": user.id,
            "email": user.email,
            "user_metadata": user.user_metadata,
            "token": token
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=f"Authentication failed: {str(e)}"
        )

async def get_optional_user(authorization: str = Header(None)) -> Optional[dict]:
    """
    Optional authentication - returns None if not authenticated
    Use for routes that work with or without auth
    """
    if not authorization or not authorization.startswith("Bearer "):
        return None
    
    try:
        return await get_current_user(authorization)
    except:
        return None
