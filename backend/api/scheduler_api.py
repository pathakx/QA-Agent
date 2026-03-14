from fastapi import APIRouter, HTTPException, Depends
from backend.services.scheduler_service import schedule_test_execution, list_jobs, delete_job
from backend.auth.project_helpers import get_current_project
import uuid

router = APIRouter()

@router.post("/schedule")
async def schedule_job(test_id: str, cron_expression: str, project: dict = Depends(get_current_project)):
    """
    Schedule a test run using cron syntax.
    Example cron: "*/5 * * * *" (run every 5 minutes)
    """
    try:
        job_id = schedule_test_execution(test_id, project['id'], cron_expression)
        return {"job_id": job_id, "status": "scheduled", "cron": cron_expression}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/jobs")
async def get_jobs():
    """List all scheduled jobs"""
    return list_jobs()

@router.delete("/jobs/{job_id}")
async def cancel_job(job_id: str):
    try:
        delete_job(job_id)
        return {"status": "cancelled"}
    except Exception:
        raise HTTPException(status_code=404, detail="Job not found")
