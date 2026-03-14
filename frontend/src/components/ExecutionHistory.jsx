import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Check, X, Layers, Activity } from 'lucide-react';
import { api } from '../lib/api';

const ExecutionHistory = () => {
    const [activeTab, setActiveTab] = useState('runs'); // 'runs' or 'batches'

    return (
        <div className="h-full flex flex-col p-6">
            <div className="flex justify-between items-center mb-6">
                <div>
                    <h2 className="text-3xl font-bold mb-2">Execution History</h2>
                    <p className="text-gray-400">View all test execution results</p>
                </div>

                <div className="flex bg-gray-900 rounded-lg p-1 border border-gray-700">
                    <button
                        onClick={() => setActiveTab('runs')}
                        className={`px-4 py-2 rounded-md flex items-center gap-2 text-sm font-medium transition ${activeTab === 'runs'
                            ? 'bg-gray-800 text-white shadow'
                            : 'text-gray-400 hover:text-gray-200'
                            }`}
                    >
                        <Activity size={16} />
                        Test Runs
                    </button>
                    <button
                        onClick={() => setActiveTab('batches')}
                        className={`px-4 py-2 rounded-md flex items-center gap-2 text-sm font-medium transition ${activeTab === 'batches'
                            ? 'bg-gray-800 text-white shadow'
                            : 'text-gray-400 hover:text-gray-200'
                            }`}
                    >
                        <Layers size={16} />
                        Batch Runs
                    </button>
                </div>
            </div>

            <div className="flex-1 overflow-hidden">
                {activeTab === 'runs' && <TestRunsList />}
                {activeTab === 'batches' && <BatchRunsList />}
            </div>
        </div>
    );
};

const TestRunsList = () => {
    const [executions, setExecutions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState('all');
    const [selectedExecution, setSelectedExecution] = useState(null);
    const [showModal, setShowModal] = useState(false);

    useEffect(() => {
        fetchExecutions();
    }, []);

    const fetchExecutions = async () => {
        setLoading(true);
        try {
            const res = await api.get('/agent/executions');
            setExecutions(res.data.executions || []);
        } catch (err) {
            console.error('Failed to fetch executions:', err);
        } finally {
            setLoading(false);
        }
    };

    const filteredExecutions = executions.filter(exec => {
        if (filter === 'all') return true;
        return exec.status === filter;
    });

    const stats = {
        total: executions.length,
        passed: executions.filter(e => e.status === 'passed').length,
        failed: executions.filter(e => e.status === 'failed').length,
        error: executions.filter(e => e.status === 'error').length
    };

    return (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="h-full flex flex-col space-y-6">
            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <StatsCard label="Total Runs" value={stats.total} color="text-indigo-400" />
                <StatsCard label="Passed" value={stats.passed} color="text-green-400" />
                <StatsCard label="Failed" value={stats.failed} color="text-red-400" />
                <StatsCard label="Errors" value={stats.error} color="text-orange-400" />
            </div>

            {/* Filters */}
            <div className="flex gap-2">
                {['all', 'passed', 'failed', 'error'].map(f => (
                    <FilterButton key={f} active={filter === f} onClick={() => setFilter(f)} label={f} />
                ))}
            </div>

            {/* Execution Table */}
            <div className="glass-panel rounded-xl flex-1 overflow-hidden flex flex-col">
                <div className="overflow-auto flex-1 custom-scrollbar">
                    {loading ? (
                        <LoadingSpinner />
                    ) : filteredExecutions.length === 0 ? (
                        <EmptyState message="No execution history yet. Run some tests to see results!" />
                    ) : (
                        <table className="w-full">
                            <thead className="bg-gray-800/50 sticky top-0">
                                <tr>
                                    <th className="text-left p-4 text-sm font-semibold text-gray-400">Test ID</th>
                                    <th className="text-left p-4 text-sm font-semibold text-gray-400">Status</th>
                                    <th className="text-left p-4 text-sm font-semibold text-gray-400">Duration</th>
                                    <th className="text-left p-4 text-sm font-semibold text-gray-400">Browser</th>
                                    <th className="text-left p-4 text-sm font-semibold text-gray-400">Started At</th>
                                    <th className="text-left p-4 text-sm font-semibold text-gray-400">Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {filteredExecutions.map((exec, idx) => (
                                    <tr key={exec.id} className="border-b border-gray-800 hover:bg-gray-800/30 transition">
                                        <td className="p-4">
                                            <span className="font-mono text-sm text-indigo-300">{exec.test_case_id}</span>
                                        </td>
                                        <td className="p-4"><StatusBadge status={exec.status} /></td>
                                        <td className="p-4 text-sm text-gray-400">
                                            {exec.duration_seconds ? `${exec.duration_seconds.toFixed(2)}s` : 'N/A'}
                                        </td>
                                        <td className="p-4 text-sm text-gray-400">
                                            {exec.browser ? `${exec.browser} ${exec.browser_version || ''}` : '-'}
                                        </td>
                                        <td className="p-4 text-sm text-gray-400">{formatDate(exec.started_at)}</td>
                                        <td className="p-4">
                                            <button
                                                onClick={() => { setSelectedExecution(exec); setShowModal(true); }}
                                                className="text-indigo-400 hover:text-indigo-300 text-sm font-medium underline"
                                            >
                                                View Details
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    )}
                </div>
            </div>

            <ExecutionDetailsModal
                show={showModal}
                onClose={() => setShowModal(false)}
                execution={selectedExecution}
            />
        </motion.div>
    );
};

const BatchRunsList = () => {
    const [batches, setBatches] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchBatches = async () => {
            try {
                const res = await api.get('/suites/batch-runs');
                setBatches(res.data.runs || []);
            } catch (err) {
                console.error('Failed to fetch batches:', err);
            } finally {
                setLoading(false);
            }
        };
        fetchBatches();
    }, []);

    return (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="h-full flex flex-col">
            <div className="glass-panel rounded-xl flex-1 overflow-hidden flex flex-col">
                <div className="overflow-auto flex-1 custom-scrollbar">
                    {loading ? (
                        <LoadingSpinner />
                    ) : batches.length === 0 ? (
                        <EmptyState message="No batch runs yet. Execute a test suite to see results!" />
                    ) : (
                        <table className="w-full">
                            <thead className="bg-gray-800/50 sticky top-0">
                                <tr>
                                    <th className="text-left p-4 text-sm font-semibold text-gray-400">Batch Name</th>
                                    <th className="text-left p-4 text-sm font-semibold text-gray-400">Status</th>
                                    <th className="text-left p-4 text-sm font-semibold text-gray-400">Progress</th>
                                    <th className="text-left p-4 text-sm font-semibold text-gray-400">Results</th>
                                    <th className="text-left p-4 text-sm font-semibold text-gray-400">Duration</th>
                                    <th className="text-left p-4 text-sm font-semibold text-gray-400">Started At</th>
                                </tr>
                            </thead>
                            <tbody>
                                {batches.map((batch) => (
                                    <tr key={batch.id} className="border-b border-gray-800 hover:bg-gray-800/30 transition">
                                        <td className="p-4">
                                            <div className="font-bold text-white">{batch.name || 'Untitled Batch'}</div>
                                            <div className="text-xs text-gray-500 font-mono">{batch.id.slice(0, 8)}</div>
                                        </td>
                                        <td className="p-4"><StatusBadge status={batch.status} /></td>
                                        <td className="p-4 w-48">
                                            <div className="flex flex-col gap-1">
                                                <div className="flex justify-between text-xs text-gray-400">
                                                    <span>{batch.passed_tests + batch.failed_tests + batch.error_tests} / {batch.total_tests}</span>
                                                    <span>{Math.round(((batch.passed_tests + batch.failed_tests + batch.error_tests) / batch.total_tests) * 100)}%</span>
                                                </div>
                                                <div className="w-full bg-gray-700 h-1.5 rounded-full overflow-hidden">
                                                    <div
                                                        className="bg-indigo-500 h-full"
                                                        style={{ width: `${((batch.passed_tests + batch.failed_tests + batch.error_tests) / batch.total_tests) * 100}%` }}
                                                    />
                                                </div>
                                            </div>
                                        </td>
                                        <td className="p-4">
                                            <div className="flex gap-2 text-xs font-bold">
                                                <span className="text-green-400">{batch.passed_tests} PASS</span>
                                                <span className="text-red-400">{batch.failed_tests} FAIL</span>
                                                <span className="text-orange-400">{batch.error_tests} ERR</span>
                                            </div>
                                        </td>
                                        <td className="p-4 text-sm text-gray-400">
                                            {batch.total_duration_seconds ? `${batch.total_duration_seconds.toFixed(2)}s` : '-'}
                                        </td>
                                        <td className="p-4 text-sm text-gray-400 text-nowrap">
                                            {formatDate(batch.started_at)}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    )}
                </div>
            </div>
        </motion.div>
    );
};

// --- Helper Components ---

const StatsCard = ({ label, value, color }) => (
    <div className="glass-panel p-4 rounded-xl">
        <div className={`text-2xl font-bold ${color}`}>{value}</div>
        <div className="text-sm text-gray-400">{label}</div>
    </div>
);

const FilterButton = ({ active, onClick, label }) => (
    <button
        onClick={onClick}
        className={`px-4 py-2 rounded-lg text-sm font-medium transition ${active ? 'bg-indigo-600 text-white' : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
            }`}
    >
        {label.charAt(0).toUpperCase() + label.slice(1)}
    </button>
);

const StatusBadge = ({ status }) => {
    const badges = {
        passed: { bg: 'bg-green-900/20', border: 'border-green-500/30', text: 'text-green-400', icon: '✅' },
        failed: { bg: 'bg-red-900/20', border: 'border-red-500/30', text: 'text-red-400', icon: '❌' },
        error: { bg: 'bg-orange-900/20', border: 'border-orange-500/30', text: 'text-orange-400', icon: '⚠️' },
        running: { bg: 'bg-blue-900/20', border: 'border-blue-500/30', text: 'text-blue-400', icon: '🔄' },
        completed: { bg: 'bg-green-900/20', border: 'border-green-500/30', text: 'text-green-400', icon: '🏁' },
        pending: { bg: 'bg-gray-800/50', border: 'border-gray-600/30', text: 'text-gray-400', icon: '⏳' },
    };
    const badge = badges[status?.toLowerCase()] || badges.pending;
    return (
        <span className={`px-3 py-1 rounded-full text-xs font-bold ${badge.bg} ${badge.border} ${badge.text} border uppercase inline-flex items-center gap-1`}>
            <span>{badge.icon}</span> {status}
        </span>
    );
};

const LoadingSpinner = () => (
    <div className="flex items-center justify-center p-12 text-gray-500">
        <span className="animate-spin text-3xl">⌛</span>
    </div>
);

const EmptyState = ({ message }) => (
    <div className="flex flex-col items-center justify-center p-12 text-gray-500">
        <Check size={48} className="mb-4 opacity-20" />
        <p>{message}</p>
    </div>
);

const formatDate = (dateStr) => {
    if (!dateStr) return 'N/A';
    return new Date(dateStr).toLocaleString();
};

const ExecutionDetailsModal = ({ show, onClose, execution }) => {
    if (!show || !execution) return null;

    return (
        <AnimatePresence>
            <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-8" onClick={onClose}>
                <motion.div
                    initial={{ scale: 0.9, y: 20, opacity: 0 }}
                    animate={{ scale: 1, y: 0, opacity: 1 }}
                    exit={{ scale: 0.9, y: 20, opacity: 0 }}
                    onClick={(e) => e.stopPropagation()}
                    className="bg-gray-900 border border-gray-700 rounded-xl p-6 max-w-4xl w-full max-h-[90vh] overflow-auto custom-scrollbar"
                >
                    <div className="flex justify-between items-start mb-6">
                        <div>
                            <h3 className="text-2xl font-bold mb-2">Execution Details</h3>
                            <p className="text-gray-400 font-mono text-sm">{execution.test_case_id}</p>
                        </div>
                        <button onClick={onClose} className="text-gray-400 hover:text-white"><X size={24} /></button>
                    </div>

                    <div className="grid grid-cols-2 gap-4 mb-6">
                        <DetailCard label="Status" content={<StatusBadge status={execution.status} />} />
                        <DetailCard label="Duration" value={execution.duration_seconds ? `${execution.duration_seconds.toFixed(2)}s` : 'N/A'} />
                        <DetailCard label="Browser" value={`${execution.browser || 'Unknown'} ${execution.browser_version || ''}`} />
                        <DetailCard label="OS" value={execution.os_info || 'Unknown'} />
                    </div>

                    {execution.screenshot_path && (
                        <div className="mb-6">
                            <h4 className="text-lg font-bold mb-3 flex items-center gap-2">📸 Screenshot</h4>
                            <div className="border border-gray-700 rounded-lg overflow-hidden">
                                <AuthenticatedImage
                                    url={`/agent/executions/${execution.id}/screenshot`}
                                    alt="Screenshot"
                                    className="w-full"
                                />
                            </div>
                        </div>
                    )}

                    {execution.video_path && (
                        <div className="mb-6">
                            <h4 className="text-lg font-bold mb-3 flex items-center gap-2">🎥 Video Recording</h4>
                            <div className="border border-gray-700 rounded-lg overflow-hidden bg-black">
                                <video
                                    controls
                                    className="w-full max-h-[500px]"
                                    src={`/api/agent/executions/${execution.id}/video`}
                                >
                                    Your browser does not support the video tag.
                                </video>
                            </div>
                        </div>
                    )}

                    {execution.error_message && (
                        <div className="mb-6">
                            <h4 className="text-lg font-bold mb-3 flex items-center gap-2 text-red-400">❌ Error</h4>
                            <div className="bg-red-950/30 border border-red-500/30 rounded-lg p-4">
                                <pre className="text-sm text-red-300 whitespace-pre-wrap font-mono">{execution.error_message}</pre>
                            </div>
                        </div>
                    )}

                    {execution.logs && (
                        <div>
                            <h4 className="text-lg font-bold mb-3">📄 Execution Logs</h4>
                            <div className="bg-black/50 border border-gray-700 rounded-lg p-4 max-h-96 overflow-auto custom-scrollbar">
                                <pre className="text-xs text-gray-300 whitespace-pre-wrap font-mono">{execution.logs}</pre>
                            </div>
                        </div>
                    )}
                </motion.div>
            </div>
        </AnimatePresence>
    );
};

const DetailCard = ({ label, value, content }) => (
    <div className="glass-panel p-4 rounded-lg">
        <div className="text-xs text-gray-500 mb-1">{label}</div>
        <div className="text-white font-semibold">{content || value}</div>
    </div>
);

export default ExecutionHistory;

const AuthenticatedImage = ({ url, alt, className }) => {
    const [src, setSrc] = useState(null);
    const [error, setError] = useState(false);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        let objectUrl = null;
        const fetchImage = async () => {
            setLoading(true);
            setError(false);
            try {
                const response = await api.get(url, { responseType: 'blob' });
                objectUrl = URL.createObjectURL(response.data);
                setSrc(objectUrl);
            } catch (e) {
                console.error("Failed to load image:", e);
                setError(true);
            } finally {
                setLoading(false);
            }
        };

        if (url) fetchImage();

        return () => {
            if (objectUrl) URL.revokeObjectURL(objectUrl);
        };
    }, [url]);

    if (error) return <div className="p-4 text-gray-500 text-center bg-gray-800/50 rounded border border-gray-700">Screenshot not available</div>;
    if (loading) return <div className="animate-pulse bg-gray-800 h-64 rounded w-full flex items-center justify-center text-gray-500">Loading screenshot...</div>;

    return <img src={src} alt={alt} className={className} />;
};
