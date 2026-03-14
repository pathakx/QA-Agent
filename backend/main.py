from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from backend.api import docs_api, agent_api, auth_api, project_api
import os
import socketio

from fastapi.middleware.cors import CORSMiddleware

# Import WebSocket manager
from backend.core.websocket_manager import sio

app = FastAPI(title="QA Testing Brain")



from fastapi.responses import JSONResponse
from fastapi.requests import Request

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback
    error_detail = traceback.format_exc()
    print(f"Global error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "trace": error_detail}
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routers
app.include_router(auth_api.router, prefix="/api/auth", tags=["authentication"])
app.include_router(project_api.router, prefix="/api", tags=["projects"])
app.include_router(docs_api.router, prefix="/api/kb", tags=["knowledge-base"])
app.include_router(agent_api.router, prefix="/api/agent", tags=["agent"])
from backend.api import execution_api
app.include_router(execution_api.router, prefix="/api/agent", tags=["execution"])
from backend.api import suite_api
app.include_router(suite_api.router, prefix="/api/suites", tags=["suites"])

# Scheduler Integration
from backend.services.scheduler_service import scheduler
from backend.api import scheduler_api
app.include_router(scheduler_api.router, prefix="/api/scheduler", tags=["scheduler"])

from backend.api import autonomous_api
app.include_router(autonomous_api.router, prefix="/api/autonomous", tags=["autonomous"])

# Test Case Management
from backend.api import testcase_api, scripts_api, results_api
app.include_router(testcase_api.router, prefix="/api/testcases", tags=["testcases"])
app.include_router(scripts_api.router, prefix="/api/scripts", tags=["scripts"])
app.include_router(results_api.router, prefix="/api/results", tags=["results"])

@app.on_event("startup")
async def start_scheduler():
    print("Starting Scheduler...")
    scheduler.start()

# Mount WebSocket as a sub-application at /ws path
# This allows Socket.IO to work without interfering with regular HTTP routes
socket_app = socketio.ASGIApp(sio, socketio_path='')
app.mount('/ws', socket_app)

# Serve Static Files
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

# Mount /assets explicitly to serve JS/CSS correctly
assets_path = os.path.join(static_dir, "assets")
if os.path.exists(assets_path):
    app.mount("/assets", StaticFiles(directory=assets_path), name="assets")

# Serve other specific static files if they exist (like vite.svg)
@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    # Prevent serving API routes as frontend
    if full_path.startswith("api") or full_path.startswith("ws"):
        return JSONResponse(status_code=404, content={"message": "Not Found"})
    
    # Check if file exists in static folder (e.g. vite.svg)
    potential_file_path = os.path.join(static_dir, full_path)
    if os.path.isfile(potential_file_path):
        return FileResponse(potential_file_path)
    
    # Serve index.html for all other routes (SPA fallback)
    return FileResponse(os.path.join(static_dir, "index.html"))

if __name__ == "__main__":
    import uvicorn
    # Run the main app, WebSocket is mounted at /ws
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8001, reload=True)
