import asyncio
from typing import List
from backend.services.execution_service import execute_test_script
from backend.core.supabase_client import create_user_client
from datetime import datetime

async def execute_suite_background(suite_id: str, project_id: str, token: str):
    """
    Execute all tests in a specific suite.
    """
    client = create_user_client(token)
    
    # 1. Get tests in suite
    tests = client.table('suite_tests').select('test_case_id').eq('suite_id', suite_id).order('execution_order').execute()
    test_ids = [t['test_case_id'] for t in tests.data]
    
    if not test_ids:
        print(f"No tests found in suite {suite_id}")
        return

    # 2. Create Batch Run
    batch_data = {
        'project_id': project_id,
        'suite_id': suite_id,
        'status': 'running',
        'total_tests': len(test_ids),
        'started_at': datetime.utcnow().isoformat()
    }
    batch_res = client.table('batch_runs').insert(batch_data).execute()
    batch_id = batch_res.data[0]['id']
    
    await _run_tests_in_batch(batch_id, test_ids, project_id, token)

async def execute_all_background(project_id: str, token: str):
    """
    Execute ALL tests in the project.
    """
    client = create_user_client(token)
    
    # 1. Get all tests with scripts
    # We need to find tests that actually have scripts generated
    scripts = client.table('selenium_scripts').select('test_case_id').eq('project_id', project_id).execute()
    # Deduplicate test_ids (in case multiple scripts per test)
    test_ids = list(set([s['test_case_id'] for s in scripts.data]))
    
    if not test_ids:
        print(f"No executable tests found in project {project_id}")
        return

    # 2. Create Batch Run
    batch_data = {
        'project_id': project_id,
        'status': 'running',
        'total_tests': len(test_ids),
        'started_at': datetime.utcnow().isoformat(),
        'name': f"Full Run {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"
    }
    batch_res = client.table('batch_runs').insert(batch_data).execute()
    batch_id = batch_res.data[0]['id']
    
    await _run_tests_in_batch(batch_id, test_ids, project_id, token)

async def _run_tests_in_batch(batch_id: str, test_ids: List[str], project_id: str, token: str):
    """
    Internal helper to run a list of tests and update batch stats.
    """
    client = create_user_client(token)
    passed = 0
    failed = 0
    error = 0
    total_duration = 0.0
    
    print(f"Starting batch run {batch_id} with {len(test_ids)} tests")
    
    for i, test_id in enumerate(test_ids):
        try:
            # Get latest script
            script_res = client.table('selenium_scripts').select('script_content').eq('project_id', project_id).eq('test_case_id', test_id).order('created_at', desc=True).limit(1).execute()
            
            if not script_res.data:
                print(f"Skipping {test_id}: No script found")
                continue
                
            script_content = script_res.data[0]['script_content']
            
            # Create execution record linked to batch
            exec_data = {
                'project_id': project_id,
                'test_case_id': test_id,
                'batch_run_id': batch_id,
                'status': 'running',
                'started_at': datetime.utcnow().isoformat()
            }
            exec_res = client.table('test_executions').insert(exec_data).execute()
            execution_id = exec_res.data[0]['id']
            
            # Execute
            from backend.services.execution_service import execute_test_script
            result = await execute_test_script(script_content)
            
            # Update Execution Record
            client.table('test_executions').update({
                'status': result.status,
                'completed_at': datetime.utcnow().isoformat(),
                'duration_seconds': result.duration,
                'logs': result.logs,
                'error_message': result.error_message,
                'screenshot_path': result.screenshot_path,
                'browser': result.browser,
                'browser_version': result.browser_version,
                'os_info': result.os_info
            }).eq('id', execution_id).execute()
            
            # Update Stats
            total_duration += result.duration
            if result.status == 'passed':
                passed += 1
            elif result.status == 'failed':
                failed += 1
            else:
                error += 1
                
            # Update Batch Run Progress
            client.table('batch_runs').update({
                'passed_tests': passed,
                'failed_tests': failed,
                'error_tests': error,
                'total_duration_seconds': total_duration
            }).eq('id', batch_id).execute()
            
            # Emit WebSocket progress if needed (optional for batch, but good for UX)
            # For now, let's rely on polling the batch run status or individual execution events
            
        except Exception as e:
            print(f"Error running test {test_id} in batch: {e}")
            error += 1
    
    # Finalize Batch Run
    client.table('batch_runs').update({
        'status': 'completed',
        'completed_at': datetime.utcnow().isoformat(),
        'passed_tests': passed,
        'failed_tests': failed,
        'error_tests': error,
        'total_duration_seconds': total_duration
    }).eq('id', batch_id).execute()
    
    print(f"Batch run {batch_id} completed")
