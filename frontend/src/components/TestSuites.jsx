import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Folder, Plus, Play, Trash, Edit, Check, X,
    ChevronRight, ChevronDown, List as ListIcon
} from 'lucide-react';
import { api } from '../lib/api';

const TestSuites = ({ availableTests }) => {
    const [suites, setSuites] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [newSuiteName, setNewSuiteName] = useState('');
    const [newSuiteDesc, setNewSuiteDesc] = useState('');
    const [selectedTests, setSelectedTests] = useState([]);
    const [expandedSuite, setExpandedSuite] = useState(null);
    const [executingSuite, setExecutingSuite] = useState(null);

    useEffect(() => {
        fetchSuites();
    }, []);

    const fetchSuites = async () => {
        try {
            setLoading(true);
            const res = await api.get('/suites/suites');
            setSuites(res.data.suites || []);
        } catch (err) {
            console.error('Failed to fetch suites:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleCreateSuite = async () => {
        try {
            await api.post('/suites/suites', {
                name: newSuiteName,
                description: newSuiteDesc,
                test_case_ids: selectedTests
            });
            setShowCreateModal(false);
            setNewSuiteName('');
            setNewSuiteDesc('');
            setSelectedTests([]);
            fetchSuites();
        } catch (err) {
            alert('Failed to create suite: ' + err.message);
        }
    };

    const handleDeleteSuite = async (suiteId, e) => {
        e.stopPropagation();
        if (!window.confirm('Are you sure you want to delete this test suite?')) return;
        try {
            await api.delete(`/suites/suites/${suiteId}`);
            fetchSuites();
        } catch (err) {
            alert('Failed to delete suite: ' + err.message);
        }
    };

    const handleRunSuite = async (suiteId, e) => {
        e.stopPropagation();
        try {
            setExecutingSuite(suiteId);
            await api.post(`/suites/suites/${suiteId}/execute`);
            alert('Suite execution started! Check Execution History for progress.');
        } catch (err) {
            alert('Failed to start execution: ' + err.message);
        } finally {
            setExecutingSuite(null);
        }
    };

    const toggleTestSelection = (testId) => {
        setSelectedTests(prev =>
            prev.includes(testId)
                ? prev.filter(id => id !== testId)
                : [...prev, testId]
        );
    };

    return (
        <div className="h-full flex flex-col p-6">
            <div className="flex justify-between items-center mb-6">
                <div>
                    <h2 className="text-2xl font-bold">Test Suites</h2>
                    <p className="text-gray-400">Organize and run tests in batches</p>
                </div>
                <button
                    onClick={() => setShowCreateModal(true)}
                    className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg flex items-center gap-2 transition"
                >
                    <Plus size={18} />
                    New Suite
                </button>
            </div>

            <div className="flex-1 overflow-auto custom-scrollbar">
                {loading ? (
                    <div className="flex justify-center p-12">
                        <span className="animate-spin text-3xl">⌛</span>
                    </div>
                ) : suites.length === 0 ? (
                    <div className="text-center py-20 bg-gray-900/50 rounded-xl border border-dashed border-gray-700">
                        <Folder size={48} className="mx-auto text-gray-600 mb-4" />
                        <h3 className="text-xl font-medium text-gray-400">No Test Suites Yet</h3>
                        <p className="text-gray-500 mt-2">Create a suite to group your tests together.</p>
                    </div>
                ) : (
                    <div className="grid gap-4">
                        {suites.map(suite => (
                            <motion.div
                                key={suite.id}
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                className="bg-gray-800/40 border border-gray-700 rounded-xl overflow-hidden"
                            >
                                <div
                                    className="p-4 flex items-center justify-between cursor-pointer hover:bg-gray-800/60 transition"
                                    onClick={() => setExpandedSuite(expandedSuite === suite.id ? null : suite.id)}
                                >
                                    <div className="flex items-center gap-3">
                                        {expandedSuite === suite.id ? <ChevronDown size={20} /> : <ChevronRight size={20} />}
                                        <div>
                                            <h3 className="font-bold text-lg">{suite.name}</h3>
                                            <p className="text-sm text-gray-400">{suite.description || 'No description'}</p>
                                        </div>
                                    </div>

                                    <div className="flex items-center gap-2">
                                        <button
                                            onClick={(e) => handleRunSuite(suite.id, e)}
                                            disabled={executingSuite === suite.id}
                                            className="bg-green-600/20 hover:bg-green-600/40 text-green-400 p-2 rounded-lg border border-green-600/30 transition flex items-center gap-2"
                                        >
                                            {executingSuite === suite.id ? (
                                                <span className="animate-spin">🔄</span>
                                            ) : (
                                                <Play size={16} />
                                            )}
                                            Run Suite
                                        </button>
                                        <button
                                            onClick={(e) => handleDeleteSuite(suite.id, e)}
                                            className="bg-red-600/20 hover:bg-red-600/40 text-red-400 p-2 rounded-lg border border-red-600/30 transition"
                                        >
                                            <Trash size={16} />
                                        </button>
                                    </div>
                                </div>

                                <AnimatePresence>
                                    {expandedSuite === suite.id && (
                                        <motion.div
                                            initial={{ height: 0 }}
                                            animate={{ height: 'auto' }}
                                            exit={{ height: 0 }}
                                            className="border-t border-gray-700 bg-black/20"
                                        >
                                            <div className="p-4">
                                                <SuiteDetails suiteId={suite.id} />
                                            </div>
                                        </motion.div>
                                    )}
                                </AnimatePresence>
                            </motion.div>
                        ))}
                    </div>
                )}
            </div>

            {/* Create Suite Modal */}
            <AnimatePresence>
                {showCreateModal && (
                    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
                        <motion.div
                            initial={{ scale: 0.9, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            exit={{ scale: 0.9, opacity: 0 }}
                            className="bg-gray-900 border border-gray-700 rounded-xl p-6 w-full max-w-2xl max-h-[90vh] flex flex-col"
                        >
                            <div className="flex justify-between items-center mb-6">
                                <h3 className="text-2xl font-bold">Create Test Suite</h3>
                                <button onClick={() => setShowCreateModal(false)} className="text-gray-400 hover:text-white">
                                    <X size={24} />
                                </button>
                            </div>

                            <div className="space-y-4 mb-6">
                                <div>
                                    <label className="block text-sm font-medium text-gray-400 mb-1">Suite Name</label>
                                    <input
                                        type="text"
                                        value={newSuiteName}
                                        onChange={(e) => setNewSuiteName(e.target.value)}
                                        className="w-full bg-black/40 border border-gray-700 rounded-lg px-4 py-2 focus:border-indigo-500 outline-none"
                                        placeholder="e.g. Smoke Tests"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-400 mb-1">Description</label>
                                    <textarea
                                        value={newSuiteDesc}
                                        onChange={(e) => setNewSuiteDesc(e.target.value)}
                                        className="w-full bg-black/40 border border-gray-700 rounded-lg px-4 py-2 focus:border-indigo-500 outline-none h-20"
                                        placeholder="Brief description of this suite..."
                                    />
                                </div>
                            </div>

                            <div className="flex-1 overflow-hidden flex flex-col min-h-0">
                                <label className="block text-sm font-medium text-gray-400 mb-2">Select Tests</label>
                                <div className="bg-black/20 border border-gray-700 rounded-lg overflow-auto flex-1 custom-scrollbar p-2">
                                    {availableTests.length === 0 ? (
                                        <div className="text-center p-8 text-gray-500">No test cases available.</div>
                                    ) : (
                                        availableTests.map(test => (
                                            <div
                                                key={test.id}
                                                onClick={() => toggleTestSelection(test.test_id)}
                                                className={`p-3 rounded-lg mb-2 cursor-pointer flex items-center justify-between border transition ${selectedTests.includes(test.test_id)
                                                        ? 'bg-indigo-900/30 border-indigo-500/50'
                                                        : 'bg-gray-800/30 border-transparent hover:bg-gray-800'
                                                    }`}
                                            >
                                                <div>
                                                    <div className="font-mono text-indigo-300 text-sm font-bold">{test.test_id}</div>
                                                    <div className="text-sm text-gray-300">{test.description}</div>
                                                </div>
                                                {selectedTests.includes(test.test_id) && (
                                                    <Check size={18} className="text-indigo-400" />
                                                )}
                                            </div>
                                        ))
                                    )}
                                </div>
                            </div>

                            <div className="flex justify-end gap-3 mt-6">
                                <button
                                    onClick={() => setShowCreateModal(false)}
                                    className="px-4 py-2 text-gray-400 hover:text-white transition"
                                >
                                    Cancel
                                </button>
                                <button
                                    onClick={handleCreateSuite}
                                    disabled={!newSuiteName}
                                    className="bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed text-white px-6 py-2 rounded-lg transition"
                                >
                                    Create Suite
                                </button>
                            </div>
                        </motion.div>
                    </div>
                )}
            </AnimatePresence>
        </div>
    );
};

const SuiteDetails = ({ suiteId }) => {
    const [tests, setTests] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchDetails = async () => {
            try {
                const res = await api.get(`/suites/suites/${suiteId}`);
                setTests(res.data.tests || []);
            } catch (err) {
                console.error(err);
            } finally {
                setLoading(false);
            }
        };
        fetchDetails();
    }, [suiteId]);

    if (loading) return <div className="text-center text-gray-500 text-sm py-4">Loading tests...</div>;

    return (
        <div>
            <h4 className="text-sm font-semibold text-gray-400 mb-3 uppercase tracking-wider">Tests in Suite ({tests.length})</h4>
            {tests.length === 0 ? (
                <p className="text-gray-500 text-sm">No tests in this suite.</p>
            ) : (
                <div className="space-y-2">
                    {tests.map((test, idx) => (
                        <div key={test.id} className="flex items-center gap-3 text-sm bg-gray-900/40 p-2 rounded">
                            <span className="bg-gray-800 text-gray-400 px-2 py-1 rounded text-xs">#{idx + 1}</span>
                            <span className="font-mono text-indigo-300">{test.test_case_id}</span>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default TestSuites;
