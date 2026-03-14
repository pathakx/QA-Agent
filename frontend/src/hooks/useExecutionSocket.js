import { useEffect, useState, useCallback } from 'react';
import io from 'socket.io-client';

let socket = null;

export const useExecutionSocket = () => {
    const [connected, setConnected] = useState(false);
    const [executionStatus, setExecutionStatus] = useState({});
    const [executionLogs, setExecutionLogs] = useState({});
    const [executionProgress, setExecutionProgress] = useState({});

    useEffect(() => {
        // Connect to WebSocket server
        const serverUrl = window.location.origin;
        socket = io(serverUrl, {
            path: '/ws/socket.io',
            transports: ['websocket', 'polling'],
        });

        socket.on('connect', () => {
            console.log('[WS] Connected to server');
            setConnected(true);
        });

        socket.on('disconnect', () => {
            console.log('[WS] Disconnected from server');
            setConnected(false);
        });

        socket.on('execution_started', (data) => {
            console.log('[WS] Execution started:', data);
            setExecutionStatus(prev => ({
                ...prev,
                [data.execution_id]: 'running'
            }));
            setExecutionLogs(prev => ({
                ...prev,
                [data.execution_id]: []
            }));
            setExecutionProgress(prev => ({
                ...prev,
                [data.execution_id]: { step: 0, total: 5, message: 'Starting...', progress: 0 }
            }));
        });

        socket.on('execution_progress', (data) => {
            console.log('[WS] Progress:', data);
            setExecutionProgress(prev => ({
                ...prev,
                [data.execution_id]: {
                    step: data.step,
                    total: data.total,
                    message: data.message,
                    progress: data.progress
                }
            }));
        });

        socket.on('execution_log', (data) => {
            console.log('[WS] Log:', data.log);
            setExecutionLogs(prev => ({
                ...prev,
                [data.execution_id]: [...(prev[data.execution_id] || []), data.log]
            }));
        });

        socket.on('execution_completed', (data) => {
            console.log('[WS] Execution completed:', data);
            setExecutionStatus(prev => ({
                ...prev,
                [data.execution_id]: data.status
            }));
            setExecutionProgress(prev => ({
                ...prev,
                [data.execution_id]: { step: data.total || 5, total: data.total || 5, message: 'Complete', progress: 100 }
            }));
        });

        return () => {
            if (socket) {
                socket.disconnect();
                socket = null;
            }
        };
    }, []);

    const subscribeToExecution = useCallback((executionId) => {
        if (socket && connected) {
            console.log('[WS] Subscribing to execution:', executionId);
            socket.emit('subscribe_execution', { execution_id: executionId });
        }
    }, [connected]);

    const unsubscribeFromExecution = useCallback((executionId) => {
        if (socket && connected) {
            console.log('[WS] Unsubscribing from execution:', executionId);
            socket.emit('unsubscribe_execution', { execution_id: executionId });
        }
    }, [connected]);

    return {
        connected,
        executionStatus,
        executionLogs,
        executionProgress,
        subscribeToExecution,
        unsubscribeFromExecution
    };
};
