"""
WebSocket manager for real-time test execution updates
"""
import socketio
from typing import Dict, Set
import asyncio

# Create Socket.IO server
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',
    logger=True,
    engineio_logger=False
)

# Track connected clients per execution
execution_subscribers: Dict[str, Set[str]] = {}

class ExecutionEventEmitter:
    """Helper class to emit execution events to WebSocket clients"""
    
    @staticmethod
    async def emit_started(execution_id: str, test_id: str, project_id: str):
        """Emit execution started event"""
        await sio.emit('execution_started', {
            'execution_id': execution_id,
            'test_id': test_id,
            'project_id': project_id,
            'timestamp': asyncio.get_event_loop().time()
        }, room=execution_id)
        print(f"[WS] Emitted execution_started for {execution_id}")
    
    @staticmethod
    async def emit_progress(execution_id: str, step: int, total: int, message: str):
        """Emit execution progress event"""
        await sio.emit('execution_progress', {
            'execution_id': execution_id,
            'step': step,
            'total': total,
            'message': message,
            'progress': int((step / total) * 100) if total > 0 else 0
        }, room=execution_id)
        print(f"[WS] Progress {execution_id}: {step}/{total} - {message}")
    
    @staticmethod
    async def emit_log(execution_id: str, log_line: str, log_type: str = 'stdout'):
        """Emit log line"""
        await sio.emit('execution_log', {
            'execution_id': execution_id,
            'log': log_line,
            'type': log_type,
            'timestamp': asyncio.get_event_loop().time()
        }, room=execution_id)
    
    @staticmethod
    async def emit_completed(execution_id: str, status: str, duration: float, error_message: str = None):
        """Emit execution completed event"""
        await sio.emit('execution_completed', {
            'execution_id': execution_id,
            'status': status,
            'duration': duration,
            'error_message': error_message,
            'timestamp': asyncio.get_event_loop().time()
        }, room=execution_id)
        print(f"[WS] Emitted execution_completed for {execution_id}: {status}")

    @staticmethod
    async def emit_agent_log(project_id: str, message: str, level: str = 'info'):
        """Emit agent log for autonomous mode"""
        # Broadcast to all connected clients (simpler for now)
        await sio.emit('agent_log', {
            'project_id': project_id,
            'message': message,
            'level': level,
            'timestamp': asyncio.get_event_loop().time()
        })
        print(f"[WS] Agent Log [{project_id}]: {message}")

# Socket.IO event handlers
@sio.event
async def connect(sid, environ):
    """Handle client connection"""
    print(f"[WS] Client connected: {sid}")

@sio.event
async def disconnect(sid):
    """Handle client disconnection"""
    print(f"[WS] Client disconnected: {sid}")
    # Remove from all execution rooms
    for execution_id, subscribers in execution_subscribers.items():
        if sid in subscribers:
            subscribers.remove(sid)

@sio.event
async def subscribe_execution(sid, data):
    """Subscribe to execution updates"""
    execution_id = data.get('execution_id')
    if execution_id:
        # Join room for this execution
        await sio.enter_room(sid, execution_id)
        
        # Track subscriber
        if execution_id not in execution_subscribers:
            execution_subscribers[execution_id] = set()
        execution_subscribers[execution_id].add(sid)
        
        print(f"[WS] Client {sid} subscribed to execution {execution_id}")
        await sio.emit('subscribed', {'execution_id': execution_id}, room=sid)

@sio.event
async def unsubscribe_execution(sid, data):
    """Unsubscribe from execution updates"""
    execution_id = data.get('execution_id')
    if execution_id:
        await sio.leave_room(sid, execution_id)
        
        if execution_id in execution_subscribers and sid in execution_subscribers[execution_id]:
            execution_subscribers[execution_id].remove(sid)
        
        print(f"[WS] Client {sid} unsubscribed from execution {execution_id}")

# Export emitter instance
emitter = ExecutionEventEmitter()
