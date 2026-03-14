import { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { Play, Terminal, CheckCircle, AlertTriangle, Cpu, FileText, Code, Gauge, CheckSquare, Square } from 'lucide-react';
import { api } from '../lib/api';
import { io } from 'socket.io-client';

const STEPS = [
    { label: "Knowledge Ingestion", trigger: "Analyzing project structure", icon: <FileText size={18} /> },
    { label: "Test Planning", trigger: "Generating test plan", icon: <Gauge size={18} /> },
    { label: "Script Generation", trigger: "Generating automation scripts", icon: <Code size={18} /> },
    { label: "Execution", trigger: "Starting test execution", icon: <Play size={18} /> },
    { label: "Reporting", trigger: "Report compiled", icon: <CheckSquare size={18} /> }
];

const AutonomousMode = () => {
    const [running, setRunning] = useState(false);
    const [logs, setLogs] = useState([]);
    const [currentStep, setCurrentStep] = useState(0);
    const logsEndRef = useRef(null);
    const [socket, setSocket] = useState(null);

    useEffect(() => {
        const newSocket = io('http://localhost:8001', {
            transports: ['websocket'],
            path: '/ws' // Make sure this matches backend mount
        });

        newSocket.on('connect', () => {
            console.log('Connected to WebSocket for logs');
        });

        newSocket.on('agent_log', (data) => {
            setLogs(prev => [...prev, data]);

            // Check for step transitions
            const message = data.message || "";
            STEPS.forEach((step, index) => {
                if (message.includes(step.trigger)) {
                    setCurrentStep(index);
                }
            });

            if (message.includes("Autonomous Run Completed") || message.includes("Autonomous Run Stopped")) {
                setRunning(false);
                if (message.includes("Completed")) {
                    setCurrentStep(STEPS.length); // Mark all as complete
                }
            }
        });

        setSocket(newSocket);

        return () => newSocket.close();
    }, []);

    useEffect(() => {
        logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [logs]);

    const startAgent = async () => {
        setRunning(true);
        setLogs([]); // Clear previous logs
        setCurrentStep(0);
        try {
            await api.post('/autonomous/start');
        } catch (e) {
            console.error(e);
            setLogs(prev => [...prev, { message: `Error starting agent: ${e.message}`, level: 'error' }]);
            setRunning(false);
        }
    };

    const stopAgent = async () => {
        try {
            await api.post('/autonomous/stop');
            // State update handled by socket message usually, but force it for responsiveness
            setLogs(prev => [...prev, { message: "🛑 Stopping agent...", level: 'warning' }]);
        } catch (e) {
            console.error(e);
            setLogs(prev => [...prev, { message: `Error stopping agent: ${e.message}`, level: 'error' }]);
        }
    };

    return (
        <div className="h-full flex flex-col p-6 space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h2 className="text-3xl font-bold mb-2 flex items-center gap-3">
                        <Cpu className="text-purple-400" />
                        Autonomous Agent
                    </h2>
                    <p className="text-gray-400">LangGraph-powered autonomous testing workflow</p>
                </div>

                <button
                    onClick={running ? stopAgent : startAgent}
                    className={`px-6 py-3 rounded-lg font-bold flex items-center gap-2 transition-all shadow-lg ${running
                        ? 'bg-red-600 hover:bg-red-700 text-white shadow-red-900/20'
                        : 'bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white shadow-purple-900/20'
                        }`}
                >
                    {running ? (
                        <>
                            <Square size={20} fill="currentColor" /> Stop Agent
                        </>
                    ) : (
                        <>
                            <Play size={20} /> Start Autonomous Testing
                        </>
                    )}
                </button>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 flex-1">
                {/* Status / Workflow Visualization */}
                <div className="lg:col-span-1 glass-panel rounded-xl p-6 flex flex-col border border-gray-800 bg-gray-900/50">
                    <h3 className="text-xl font-bold mb-6 text-gray-200">Workflow Status</h3>
                    <div className="space-y-4">
                        {STEPS.map((step, index) => {
                            let status = 'pending';
                            if (index < currentStep) status = 'completed';
                            if (index === currentStep && running) status = 'active';
                            if (index === currentStep && !running && currentStep === STEPS.length) status = 'completed'; // All done

                            return (
                                <StepItem
                                    key={index}
                                    label={step.label}
                                    icon={step.icon}
                                    status={status}
                                />
                            );
                        })}
                    </div>
                </div>

                {/* Terminal / Logs */}
                <div className="lg:col-span-2 glass-panel rounded-xl p-0 flex flex-col overflow-hidden bg-black border border-gray-800 shadow-2xl">
                    <div className="bg-gray-900 px-4 py-3 border-b border-gray-800 flex items-center justify-between">
                        <span className="text-xs font-mono text-gray-400 flex items-center gap-2">
                            <Terminal size={14} className="text-green-500" /> agent_output.log
                        </span>
                        <div className="flex gap-2">
                            <div className="w-3 h-3 rounded-full bg-red-500/20 border border-red-500/50"></div>
                            <div className="w-3 h-3 rounded-full bg-yellow-500/20 border border-yellow-500/50"></div>
                            <div className="w-3 h-3 rounded-full bg-green-500/20 border border-green-500/50"></div>
                        </div>
                    </div>
                    <div className="flex-1 p-4 font-mono text-sm overflow-auto custom-scrollbar">
                        {logs.length === 0 && (
                            <div className="text-gray-600 italic p-4 text-center">Waiting for agent to start...</div>
                        )}
                        {logs.map((log, i) => (
                            <div key={i} className={`mb-1.5 break-words ${log.level === 'error' ? 'text-red-400' : 'text-gray-300'}`}>
                                <span className="text-gray-600 mr-3 select-none">[{new Date().toLocaleTimeString()}]</span>
                                {log.message}
                            </div>
                        ))}
                        <div ref={logsEndRef} />
                    </div>
                </div>
            </div>
        </div>
    );
};

const StepItem = ({ label, icon, status }) => {
    let statusIcon = <div className="w-5 h-5 rounded-full border-2 border-gray-700" />;
    let color = "text-gray-500";
    let bgColor = "bg-transparent";
    let borderColor = "border-transparent";

    if (status === 'active') {
        statusIcon = <div className="w-5 h-5 rounded-full border-2 border-purple-500 border-t-transparent animate-spin" />;
        color = "text-purple-300 font-bold";
        bgColor = "bg-purple-900/20";
        borderColor = "border-purple-500/30";
    } else if (status === 'completed') {
        statusIcon = <CheckCircle size={20} className="text-green-400" />;
        color = "text-green-300";
        bgColor = "bg-green-900/10";
        borderColor = "border-green-500/20";
    }

    return (
        <div className={`flex items-center gap-3 p-3 rounded-lg border transition-all duration-300 ${bgColor} ${borderColor}`}>
            {status === 'pending' ? <div className="text-gray-600">{icon}</div> : <div className={status === 'completed' ? 'text-green-400' : 'text-purple-400'}>{icon}</div>}
            <div className="flex-1 flex justify-between items-center">
                <span className={color}>{label}</span>
                {statusIcon}
            </div>
        </div>
    );
}

export default AutonomousMode;
