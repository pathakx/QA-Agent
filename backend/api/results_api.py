import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from backend.auth.dependencies import get_current_user
from backend.core.supabase_client import create_user_client
from backend.auth.project_helpers import get_current_project
from enum import Enum
from typing import List, Optional

class TestType(str, Enum):
    AUTONOMOUS = "autonomous"
    MANUAL = "manual"

router = APIRouter()

@router.get("/video/{execution_id}")
async def get_execution_video(
    execution_id: str,
    project: dict = Depends(get_current_project),
    user: dict = Depends(get_current_user)
):
    """Stream video for a test execution"""
    try:
        user_client = create_user_client(user['token'])
        
        # Verify execution belongs to project
        res = user_client.table('test_executions').select('video_path').eq('id', execution_id).eq('project_id', project['id']).single().execute()
        
        if not res.data or not res.data.get('video_path'):
            raise HTTPException(status_code=404, detail="Video record not found")
            
        video_path = res.data['video_path']
        
        # Fix path if it is relative or needs adjustment
        # If path is stored as absolute, use it. If relative, join with base.
        # Assuming absolute path for now as stored by selenium service.
        
        if not os.path.exists(video_path):
            raise HTTPException(status_code=404, detail=f"Video file missing from storage")
            
        return FileResponse(video_path, media_type="video/webm")
    except Exception as e:
        print(f"Error serving video: {e}")
        raise HTTPException(status_code=404, detail="Video not found")

@router.get("/")
async def get_test_results(
    type: TestType,
    project: dict = Depends(get_current_project),
    user: dict = Depends(get_current_user)
):
    """
    Get generic test results filtered by type.
    We try to filter by 'source' in testcases, but fallback to 'status'.
    """
    try:
        user_client = create_user_client(user['token'])
        
        # We assume 'agent' means autonomous, 'manual' means manual.
        # If 'source' column isn't populated, we fallback to guessing by ID format or returning all.
        
        target_source = 'agent' if type == TestType.AUTONOMOUS else 'manual'
        
        # Join with testcases to get source
        # select=*,testcases!inner(test_id, source)
        response = user_client.table('test_executions').select(
            '*, testcases!inner(test_id, source, feature)'
        ).eq('project_id', project['id']).order('executed_at', desc=True).execute()
        
        all_results = response.data or []
        
        filtered_results = []
        for res in all_results:
            tc = res.get('testcases')
            source = tc.get('source', 'manual') if tc else 'manual'
            
            # Normalization
            if source == 'autonomous': source = 'agent'
            
            if target_source == 'agent' and source == 'agent':
                filtered_results.append(res)
            elif target_source == 'manual' and source != 'agent':
                filtered_results.append(res)
                
        return filtered_results

    except Exception as e:
        print(f"Error getting results: {e}")
        return []
