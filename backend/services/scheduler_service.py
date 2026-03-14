from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.triggers.cron import CronTrigger
import os
import uuid
from datetime import datetime
from backend.core.supabase_client import create_client
from backend.services.execution_service import execute_test_script

# Initialize scheduler
scheduler = AsyncIOScheduler()

# Initialize DB for jobs
if not os.path.exists('jobs.sqlite'):
    open('jobs.sqlite', 'w').close()

scheduler.add_jobstore('sqlalchemy', url='sqlite:///jobs.sqlite')

def get_service_client():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    return create_client(url, key)

async def execute_scheduled_job(test_id: str, project_id: str):
    """
    Execute a scheduled test job independent of user session
    """
    try:
        print(f"[SCHEDULER] Executing test {test_id} for project {project_id}")
        client = get_service_client()
        
        # Fetch script
        # Note: Using service role key bypasses RLS, so we must be careful with project scoping
        script_res = client.table('selenium_scripts').select('script_content').eq(
            'project_id', project_id
        ).eq('test_case_id', test_id).order('created_at', desc=True).limit(1).execute()
        
        if not script_res.data:
            print(f"[SCHEDULER] No script found for test {test_id}")
            return
            
        script_content = script_res.data[0]['script_content']
        
        # Create execution record
        exec_data = {
            'project_id': project_id,
            'test_case_id': test_id,
            'status': 'running',
            'started_at': datetime.utcnow().isoformat(),
            'notes': 'Scheduled Execution'
        }
        
        exec_res = client.table('test_executions').insert(exec_data).execute()
        execution_id = exec_res.data[0]['id']
        
        # Execute script
        result = await execute_test_script(script_content)
        
        # Update record
        client.table('test_executions').update({
            'status': result.status,
            'completed_at': datetime.utcnow().isoformat(),
            'duration_seconds': result.duration,
            'logs': result.logs,
            'error_message': result.error_message,
            'screenshot_path': result.screenshot_path,
            'video_path': result.video_path,
            'browser': result.browser,
            'browser_version': result.browser_version,
            'os_info': result.os_info
        }).eq('id', execution_id).execute()
        
        print(f"[SCHEDULER] Job completed for {test_id}: {result.status}")
        
    except Exception as e:
        print(f"[SCHEDULER] Job failed: {e}")

def schedule_test_execution(test_id: str, project_id: str, cron_expression: str):
    """
    Schedule a test execution using cron expression
    """
    job_id = f"job_{test_id}_{uuid.uuid4().hex[:8]}"
    scheduler.add_job(
        execute_scheduled_job,
        CronTrigger.from_crontab(cron_expression),
        id=job_id,
        args=[test_id, project_id],
        replace_existing=True
    )
    return job_id

def list_jobs():
    return [{"id": job.id, "next_run": str(job.next_run_time)} for job in scheduler.get_jobs()]

def delete_job(job_id: str):
    scheduler.remove_job(job_id)
