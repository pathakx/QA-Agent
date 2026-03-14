"""
Authentication API endpoints
Handles user profile and session management
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from backend.auth.dependencies import get_current_user
from backend.core.supabase_client import supabase, create_user_client

router = APIRouter()

class ProfileUpdate(BaseModel):
    full_name: str

@router.get("/me")
async def get_current_user_profile(current_user = Depends(get_current_user)):
    """Get current user's profile"""
    try:
        # Get profile from Supabase
        user_client = create_user_client(current_user['token'])
        
        response = user_client.table('profiles').select('*').eq(
            'id', current_user['user_id']
        ).single().execute()
        
        if response.data:
            return {
                "user": {
                    "id": current_user['user_id'],
                    "email": current_user['email'],
                    "full_name": response.data.get('full_name'),
                    "avatar_url": response.data.get('avatar_url'),
                    "created_at": response.data.get('created_at')
                }
            }
        else:
            # Profile doesn't exist yet, return basic info
            return {
                "user": {
                    "id": current_user['user_id'],
                    "email": current_user['email'],
                    "full_name": current_user.get('user_metadata', {}).get('full_name'),
                }
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch profile: {str(e)}")

@router.put("/me")
async def update_profile(
    profile: ProfileUpdate,
    current_user = Depends(get_current_user)
):
    """Update current user's profile"""
    try:
        user_client = create_user_client(current_user['token'])
        
        response = user_client.table('profiles').update({
            'full_name': profile.full_name
        }).eq('id', current_user['user_id']).execute()
        
        return {"success": True, "message": "Profile updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update profile: {str(e)}")

@router.post("/logout")
async def logout(current_user = Depends(get_current_user)):
    """Logout endpoint (client-side handles token deletion)"""
    # With Supabase, logout is handled client-side by clearing the session
    # This endpoint is just for consistency
    return {"success": True, "message": "Logged out successfully"}
