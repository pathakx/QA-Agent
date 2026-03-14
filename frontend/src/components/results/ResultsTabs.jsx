import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle, XCircle, AlertTriangle, Play, Calendar, Clock, Terminal, Activity, FileText, X, Video } from 'lucide-react';
import { api } from '../../lib/api';

const ResultsTabs = () => {
    const [activeTab, setActiveTab] = useState('autonomous');
    const [results, setResults] = useState([]);
    const [loading, setLoading] = useState(false);
    const [selectedResult, setSelectedResult] = useState(null);

    useEffect(() => {
        fetchResults();
    }, [activeTab]);

    const fetchResults = async () => {
        setLoading(true);
        try {
            const response = await api.get(`/results?type=${activeTab}`);
            setResults(response.data || []);
        } catch (error) {
            console.error("Failed to fetch results", error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="h-full flex flex-col p-6 space-y-6 relative">
            <div className="flex justify-between items-center">
                <div>
                    <h2 className="text-3xl font-bold mb-2 flex items-center gap-3">
                        <Activity className="text-blue-400" />
                        Test Results
                    </h2>
                    <p className="text-gray-400">View execution history and reports</p>
                </div>
            </div>

            {/* Tabs */}
            <div className="flex space-x-4 border-b border-gray-700">
                <button
                    onClick={() => setActiveTab('autonomous')}
                    className={`pb-3 px-4 text-lg font-medium transition-colors relative ${activeTab === 'autonomous' ? 'text-blue-400' : 'text-gray-400 hover:text-white'
                        }`}
                >
                    Autonomous Results
                    {activeTab === 'autonomous' && (
                        <motion.div layoutId="underline" className="absolute bottom-0 left-0 right-0 h-1 bg-blue-400 rounded-t-full" />
                    )}
                </button>
                <button
                    onClick={() => setActiveTab('manual')}
                    className={`pb-3 px-4 text-lg font-medium transition-colors relative ${activeTab === 'manual' ? 'text-green-400' : 'text-gray-400 hover:text-white'
                        }`}
                >
                    Manual Run Results
                    {activeTab === 'manual' && (
                        <motion.div layoutId="underline" className="absolute bottom-0 left-0 right-0 h-1 bg-green-400 rounded-t-full" />
                    )}
                </button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-auto custom-scrollbar">
                {loading ? (
                    <div className="flex justify-center items-center h-64">
                        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
                    </div>
                ) : results.length === 0 ? (
                    <div className="text-center py-20 text-gray-500">
                        <FileText size={48} className="mx-auto mb-4 opacity-50" />
                        <p>No {activeTab} test results found.</p>
                    </div>
                ) : (
                    <div className="space-y-4">
                        {results.map((result) => (
                            <ResultCard
                                key={result.id}
                                result={result}
                                type={activeTab}
                                onSelect={() => setSelectedResult(result)}
                            />
                        ))}
                    </div>
                )}
            </div>

            {/* Modal */}
            <AnimatePresence>
                {selectedResult && (
                    <ResultDetailModal result={selectedResult} onClose={() => setSelectedResult(null)} />
                )}
            </AnimatePresence>
        </div>
    );
};

const ResultCard = ({ result, type, onSelect }) => {
    const statusColor = result.status === 'passed' ? 'text-green-400' : result.status === 'failed' ? 'text-red-400' : 'text-yellow-400';
    const StatusIcon = result.status === 'passed' ? CheckCircle : result.status === 'failed' ? XCircle : AlertTriangle;

    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-gray-800 p-5 rounded-xl border border-gray-700 hover:border-indigo-500/50 transition-colors cursor-pointer"
            onClick={onSelect}
        >
            <div className="flex justify-between items-start">
                <div>
                    <div className="flex items-center gap-3 mb-2">
                        <StatusIcon className={statusColor} size={20} />
                        <h3 className="tex-xl font-semibold">{result.test_case_id}</h3>
                        <span className={`px-2 py-0.5 text-xs rounded-full border ${result.status === 'passed' ? 'bg-green-900/30 border-green-800 text-green-300' :
                            result.status === 'failed' ? 'bg-red-900/30 border-red-800 text-red-300' :
                                'bg-yellow-900/30 border-yellow-800 text-yellow-300'
                            }`}>
                            {result.status.toUpperCase()}
                        </span>
                    </div>
                    {result.testcases?.feature && (
                        <div className="text-xs text-indigo-300 mb-1 font-mono">{result.testcases.feature}</div>
                    )}
                    <p className="text-gray-400 text-sm mb-3 line-clamp-2">{result.error_message || "Test executed successfully."}</p>

                    <div className="flex items-center gap-4 text-xs text-gray-500">
                        <span className="flex items-center gap-1"><Calendar size={12} /> {new Date(result.executed_at).toLocaleDateString()}</span>
                        <span className="flex items-center gap-1"><Clock size={12} /> {new Date(result.executed_at).toLocaleTimeString()}</span>
                        {result.duration && <span className="flex items-center gap-1"><Activity size={12} /> {result.duration}s</span>}
                    </div>
                </div>

                <div className="flex gap-2">
                    {result.video_path && (
                        <button className="p-2 bg-gray-700 rounded-lg hover:bg-gray-600 text-blue-300" title="Has Video">
                            <Video size={16} />
                        </button>
                    )}
                    <button className="p-2 bg-gray-700 rounded-lg hover:bg-gray-600 text-gray-300" title="View Details">
                        <Terminal size={16} />
                    </button>
                </div>
            </div>
        </motion.div>
    );
};

const ResultDetailModal = ({ result, onClose }) => {
    // Construct video URL assuming backend serves it at /api/results/video/{id}
    // const videoUrl = `http://localhost:8001/api/results/video/${result.id}`; 
    // Using a simpler direct serve for now if possible, but let's assume we implement the endpoint.
    const videoUrl = `${api.defaults.baseURL || 'http://localhost:8001/api'}/results/video/${result.id}`;

    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4"
            onClick={onClose}
        >
            <motion.div
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.9, opacity: 0 }}
                className="bg-gray-900 border border-gray-700 rounded-2xl w-full max-w-4xl h-[80vh] flex flex-col shadow-2xl overflow-hidden"
                onClick={e => e.stopPropagation()}
            >
                {/* Header */}
                <div className="p-6 border-b border-gray-800 flex justify-between items-center bg-gray-800/50">
                    <div>
                        <h2 className="text-2xl font-bold text-white flex items-center gap-3">
                            {result.test_case_id}
                            <span className={`text-sm px-3 py-1 rounded-full border ${result.status === 'passed' ? 'bg-green-900/30 border-green-800 text-green-300' :
                                result.status === 'failed' ? 'bg-red-900/30 border-red-800 text-red-300' :
                                    'bg-yellow-900/30 border-yellow-800 text-yellow-300'
                                }`}>
                                {result.status.toUpperCase()}
                            </span>
                        </h2>
                        <div className="text-gray-400 text-sm mt-1 flex gap-4">
                            <span>Executed: {new Date(result.executed_at).toLocaleString()}</span>
                            {result.testcases?.feature && <span>Feature: {result.testcases.feature}</span>}
                        </div>
                    </div>
                    <button onClick={onClose} className="p-2 hover:bg-gray-700 rounded-full text-gray-400 hover:text-white transition">
                        <X size={24} />
                    </button>
                </div>

                {/* Body */}
                <div className="flex-1 overflow-y-auto p-6 space-y-6">
                    {/* Video Section */}
                    {result.video_path ? (
                        <div className="bg-black rounded-xl overflow-hidden border border-gray-800 shadow-lg relative group">
                            <div className="aspect-video">
                                <video
                                    src={videoUrl}
                                    controls
                                    className="w-full h-full object-contain"
                                    poster="https://placehold.co/600x400/1f2937/9ca3af?text=Video+Loading"
                                >
                                    Your browser does not support the video tag.
                                </video>
                            </div>
                            <div className="p-2 bg-gray-900 text-xs text-gray-500 font-mono break-all border-t border-gray-800">
                                Source: {result.video_path}
                            </div>
                        </div>
                    ) : (
                        <div className="bg-gray-800/50 rounded-xl p-8 text-center text-gray-500 border border-dashed border-gray-700">
                            <Video size={48} className="mx-auto mb-4 opacity-20" />
                            <p>No video recording available for this execution.</p>
                        </div>
                    )}

                    {/* Logs Section */}
                    <div>
                        <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                            <Terminal size={18} className="text-indigo-400" /> Execution Logs
                        </h3>
                        <div className="bg-gray-950 rounded-lg border border-gray-800 p-4 font-mono text-xs overflow-x-auto text-gray-300 leading-relaxed whitespace-pre-wrap max-h-96 custom-scrollbar">
                            {result.logs || result.error_message || "No logs available."}
                        </div>
                    </div>
                </div>
            </motion.div>
        </motion.div>
    );
};

export default ResultsTabs;
