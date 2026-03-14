import { useState, useEffect, useContext } from 'react';
import axios from 'axios';
import {
  Database,
  TestTube,
  Code,
  Brain,
  Upload,
  Trash,
  Download,
  Check,
  X,
  LogOut,
  User,
  Folder,
  Play,
  Settings,
  ChevronRight,
  Layout,
  Sun,
  Moon,
  Cpu,
  Activity
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { AuthProvider, AuthContext } from './contexts/AuthContext';
import { ProjectProvider, ProjectContext } from './contexts/ProjectContext';
import { AuthPage } from './components/AuthPage';
import { ProjectSwitcher } from './components/ProjectSwitcher';

// --- SVGs for Icons ---
// Using Lucide React components instead

// --- API Helpers ---
import { api } from './lib/api';
import { useExecutionSocket } from './hooks/useExecutionSocket';

// --- Components ---
import TestSuites from './components/TestSuites';
import ExecutionHistory from './components/ExecutionHistory';

import AutonomousMode from './components/AutonomousMode';
import ResultsTabs from './components/results/ResultsTabs';

const Sidebar = ({ activeTab, setActiveTab }) => {
  const { user, signOut } = useContext(AuthContext);
  const tabs = [
    { id: 'kb', label: 'Knowledge Base', icon: Database },
    { id: 'tests', label: 'Test Generator', icon: TestTube },
    { id: 'scripts', label: 'Selenium Scripts', icon: Code },
    { id: 'suites', label: 'Test Suites', icon: Folder }, // New items
    { id: 'autonomous', label: 'Autonomous Agent', icon: Cpu },
    { id: 'results', label: 'Test Results', icon: Activity },
    { id: 'history', label: 'Execution History', icon: Check },
  ];

  const handleLogout = async () => {
    try {
      await signOut();
    } catch (error) {
      console.error('Logout error:', error);
    }
  };

  return (
    <div className="w-64 h-screen bg-gray-900 border-r border-gray-800 flex flex-col p-4 fixed left-0 top-0 z-50">
      <div className="flex items-center gap-3 mb-8 px-2">
        <div className="text-indigo-500"><Brain size={32} /></div>
        <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 to-purple-400">
          QA Agent
        </h1>
      </div>

      {/* Project Switcher */}
      <ProjectSwitcher />

      <nav className="space-y-2 flex-1 mt-4">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 ${activeTab === tab.id
              ? 'bg-indigo-600/20 text-indigo-400 border border-indigo-500/30'
              : 'text-gray-400 hover:bg-gray-800 hover:text-gray-200'
              }`}
          >
            <tab.icon size={20} />
            <span className="font-medium">{tab.label}</span>
          </button>
        ))}
      </nav>

      {/* User Profile */}
      <div className="mt-auto space-y-3">
        <div className="p-4 bg-gray-800/50 rounded-lg border border-gray-700">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-full bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center">
              <User size={20} className="text-indigo-400" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-sm font-medium text-white truncate">
                {user?.user_metadata?.full_name || user?.email?.split('@')[0]}
              </div>
              <div className="text-xs text-gray-500 truncate">{user?.email}</div>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg bg-gray-700/50 hover:bg-gray-700 text-gray-300 hover:text-white text-sm font-medium transition"
          >
            <LogOut size={16} />
            Sign Out
          </button>
        </div>
      </div>
    </div>
  );
};

const KnowledgeBase = () => {
  const [status, setStatus] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [building, setBuilding] = useState(false);
  const [resetting, setResetting] = useState(false);

  const { currentProject } = useContext(ProjectContext);

  const fetchStatus = async () => {
    if (!currentProject) return;
    try {
      const res = await api.get('/kb/status');
      setStatus(res.data);
    } catch (err) {
      console.error("Failed to fetch status", err);
    }
  };

  useEffect(() => {
    if (currentProject) {
      fetchStatus();
      const interval = setInterval(fetchStatus, 10000);
      return () => clearInterval(interval);
    } else {
      setStatus(null);
    }
  }, [currentProject]);

  if (!currentProject) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex flex-col items-center justify-center h-full text-gray-500"
      >
        <Database size={64} className="mb-4 opacity-20" />
        <h2 className="text-2xl font-bold text-gray-400 mb-2">No Project Selected</h2>
        <p>Please select or create a project from the sidebar to manage files.</p>
      </motion.div>
    );
  }

  const handleFileUpload = async (event, type) => {
    const files = event.target.files;
    if (!files.length) return;

    setUploading(true);
    const formData = new FormData();

    try {
      const endpoint = type === 'html' ? '/kb/html/upload' : '/kb/docs/upload';
      for (let file of files) {
        const fd = new FormData();
        fd.append('file', file);
        await api.post(endpoint, fd);
      }
      await fetchStatus();
      await fetchStatus();
      // Automatically build after upload
      await handleBuild();
    } catch (err) {
      alert('Upload failed: ' + err.message);
    } finally {
      setUploading(false);
      // Reset input
      event.target.value = null;
    }
  };

  const handleBuild = async () => {
    setBuilding(true);
    try {
      const res = await api.get('/kb/build');
      if (res.data.status === 'error') throw new Error(res.data.error);
      alert(`Knowledge Base Built! Embeddings: ${res.data.embedding_count}`);
      await fetchStatus();
    } catch (err) {
      alert('Build failed: ' + err.message);
    } finally {
      setBuilding(false);
    }
  };

  const handleReset = async () => {
    if (!confirm("Are you sure? This will delete all files and embeddings.")) return;
    setResetting(true);
    try {
      await api.post('/kb/reset');
      await fetchStatus();
    } catch (err) {
      alert('Reset failed: ' + err.message);
    } finally {
      setResetting(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6 p-8"
    >
      <h2 className="text-3xl font-bold mb-6">Knowledge Base Management</h2>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="glass-panel p-6 rounded-xl">
          <div className="text-gray-400 mb-2">Documents</div>
          <div className="text-3xl font-bold">{status?.doc_count || 0}</div>
        </div>
        <div className="glass-panel p-6 rounded-xl">
          <div className="text-gray-400 mb-2">HTML Files</div>
          <div className="text-3xl font-bold">{status?.html_files?.length || 0}</div>
        </div>
        <div className="glass-panel p-6 rounded-xl">
          <div className="text-gray-400 mb-2">Vector Embeddings</div>
          <div className="text-3xl font-bold text-indigo-400">{status?.embedding_count || 0}</div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-8">
        <div className="glass-panel p-6 rounded-xl">
          <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <span className="bg-indigo-500/20 p-2 rounded text-indigo-400"><Upload size={18} /></span>
            Upload Documents
          </h3>
          <p className="text-sm text-gray-400 mb-4">Support PDF, TXT, MD, JSON</p>
          <label className="block w-full border-2 border-dashed border-gray-600 rounded-lg p-8 text-center hover:border-indigo-500 hover:bg-gray-800/50 transition cursor-pointer group">
            <input type="file" multiple className="hidden" onChange={(e) => handleFileUpload(e, 'doc')} accept=".pdf,.txt,.md,.json" />
            <div className="text-gray-300 font-medium group-hover:text-indigo-400 transition">Click to upload documents</div>
          </label>
        </div>

        <div className="glass-panel p-6 rounded-xl">
          <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <span className="bg-purple-500/20 p-2 rounded text-purple-400"><Code size={18} /></span>
            Upload HTML
          </h3>
          <p className="text-sm text-gray-400 mb-4">Required for UI Element extraction</p>
          <label className="block w-full border-2 border-dashed border-gray-600 rounded-lg p-8 text-center hover:border-purple-500 hover:bg-gray-800/50 transition cursor-pointer group">
            <input type="file" multiple className="hidden" onChange={(e) => handleFileUpload(e, 'html')} accept=".html,.htm" />
            <div className="text-gray-300 font-medium group-hover:text-purple-400 transition">Click to upload HTML files</div>
          </label>
        </div>
      </div>

      <div className="flex gap-4 mt-8">
        <button
          onClick={handleBuild}
          disabled={building}
          className="bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-3 rounded-lg font-medium shadow-lg shadow-indigo-500/30 flex items-center gap-2 transition disabled:opacity-50"
        >
          {building ? <span className="animate-spin">⌛</span> : <Database size={18} />}
          {building ? 'Building...' : 'Build Knowledge Base'}
        </button>

        <button
          onClick={handleReset}
          disabled={resetting}
          className="bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/50 px-6 py-3 rounded-lg font-medium flex items-center gap-2 transition disabled:opacity-50"
        >
          <Trash size={18} />
          Reset Database
        </button>
      </div>

      <div className="mt-8">
        <h3 className="text-xl font-semibold mb-4">Uploaded Files</h3>
        <div className="glass-panel rounded-xl overflow-hidden">
          <table className="w-full text-left border-collapse">
            <thead className="bg-gray-800 text-gray-400 text-sm">
              <tr>
                <th className="p-4">Filename</th>
                <th className="p-4">Type</th>
                <th className="p-4">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-700">
              {status?.doc_files?.map(f => (
                <tr key={f} className="hover:bg-gray-800/50 transition">
                  <td className="p-4">{f}</td>
                  <td className="p-4 text-sm text-gray-400">Document</td>
                  <td className="p-4"><span className="text-green-400 text-xs bg-green-900/30 px-2 py-1 rounded inline-flex items-center gap-1"><Check size={12} /> Uploaded</span></td>
                </tr>
              ))}
              {status?.html_files?.map(f => (
                <tr key={f} className="hover:bg-gray-800/50 transition">
                  <td className="p-4">{f}</td>
                  <td className="p-4 text-sm text-gray-400">HTML Source</td>
                  <td className="p-4"><span className="text-purple-400 text-xs bg-purple-900/30 px-2 py-1 rounded inline-flex items-center gap-1"><Check size={12} /> Uploaded</span></td>
                </tr>
              ))}
              {(!status?.doc_files?.length && !status?.html_files?.length) && (
                <tr>
                  <td colSpan="3" className="p-8 text-center text-gray-500">No files uploaded yet.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </motion.div>
  );
};

const TestGenerator = ({ setGeneratedTests }) => {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [tests, setTests] = useState([]);
  const [error, setError] = useState(null);

  const { currentProject } = useContext(ProjectContext);

  // Load saved test cases on mount or when project changes
  useEffect(() => {
    const loadSavedTests = async () => {
      if (!currentProject) {
        setTests([]);
        setGeneratedTests([]);
        return;
      }

      try {
        const res = await api.get('/agent/testcases');
        if (res.data.testcases) {
          const loadedTests = Array.isArray(res.data.testcases) ? res.data.testcases : [];
          setTests(loadedTests);
          setGeneratedTests(loadedTests);
        } else {
          setTests([]);
          setGeneratedTests([]);
        }
      } catch (err) {
        console.error('Failed to load saved test cases:', err);
        // Don't clear tests on error to avoid flashing empty state if it's a transient network error
        // But if it's 404/401, maybe we should?
      }
    };
    loadSavedTests();
  }, [currentProject, setGeneratedTests]);

  if (!currentProject) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-gray-500">
        <Brain size={64} className="mb-4 opacity-20" />
        <h2 className="text-2xl font-bold text-gray-400 mb-2">No Project Selected</h2>
        <p>Please select or create a project from the sidebar.</p>
      </div>
    );
  }

  const handleGenerate = async () => {
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const res = await api.post('/agent/testcases', { query });
      if (res.data.error) throw new Error(res.data.error);

      // Ensure we have an array and sort by test_id
      const testcases = Array.isArray(res.data.testcases) ? res.data.testcases : [];
      const sortedTests = testcases.sort((a, b) => {
        const idA = String(a.test_id || '');
        const idB = String(b.test_id || '');
        return idA.localeCompare(idB);
      });

      setTests(sortedTests);
      setGeneratedTests(sortedTests);
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateAll = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.post('/agent/testcases', { query: "generate comprehensive test cases for all features in the application" });
      if (res.data.error) throw new Error(res.data.error);

      // Ensure we have an array and sort by test_id
      const testcases = Array.isArray(res.data.testcases) ? res.data.testcases : [];
      const sortedTests = testcases.sort((a, b) => {
        const idA = String(a.test_id || '');
        const idB = String(b.test_id || '');
        return idA.localeCompare(idB);
      });

      setTests(sortedTests);
      setGeneratedTests(sortedTests);
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleClearAll = async () => {
    if (!confirm("Are you sure you want to clear all test cases for this project? This action cannot be undone.")) return;

    setLoading(true);
    try {
      await api.delete('/testcases/all/clear');
      setTests([]);
      setGeneratedTests([]);
    } catch (err) {
      console.error('Failed to clear test cases:', err);
      setError('Failed to clear test cases: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="space-y-6 p-8 h-full flex flex-col"
    >
      <div className="flex flex-col gap-4">
        <h2 className="text-3xl font-bold">Test Case Generator</h2>
        <div className="flex gap-4">
          <div className="glass-panel p-1 rounded-xl flex flex-1 items-center bg-gray-800/50 border border-gray-700 focus-within:border-indigo-500 transition shadow-lg">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Describe specific feature (e.g. 'Login page')..."
              className="w-full bg-transparent p-4 outline-none text-lg text-white placeholder-gray-500"
              onKeyDown={(e) => e.key === 'Enter' && handleGenerate()}
            />
            <button
              onClick={handleGenerate}
              disabled={loading}
              className="bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-3 rounded-lg font-medium m-1 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 shadow-lg shadow-indigo-500/20 whitespace-nowrap"
            >
              {loading && <span className="animate-spin">⌛</span>}
              Generate
            </button>
          </div>

          <button
            onClick={handleGenerateAll}
            disabled={loading}
            className="glass-panel px-6 py-3 rounded-xl font-medium border border-purple-500/30 text-purple-300 hover:bg-purple-500/10 hover:border-purple-500/50 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 shadow-lg whitespace-nowrap"
          >
            {loading ? <span className="animate-spin">⌛</span> : <Brain size={20} />}
            Generate All Test Cases
          </button>

          <button
            onClick={handleClearAll}
            disabled={loading || tests.length === 0}
            className="glass-panel px-6 py-3 rounded-xl font-medium border border-red-500/30 text-red-300 hover:bg-red-500/10 hover:border-red-500/50 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 shadow-lg whitespace-nowrap"
          >
            <Trash size={20} />
            Clear All
          </button>
        </div>
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-red-500/10 border border-red-500/50 text-red-200 p-4 rounded-lg flex items-center gap-3"
          >
            <X size={20} className="text-red-400" />
            {error}
          </motion.div>
        )}
      </div>

      <div className="flex-1 overflow-y-auto custom-scrollbar space-y-4 pr-2 pb-20">
        {tests.length === 0 && !loading && !error && (
          <div className="flex flex-col items-center justify-center h-64 text-gray-500 mt-20">
            <Brain size={64} className="mb-4 opacity-20" />
            <p className="text-xl">Enter a prompt to generate AI-powered test cases.</p>
          </div>
        )}

        <AnimatePresence>
          {tests.map((test, idx) => (
            <motion.div
              key={idx}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: idx * 0.1 }}
              className="glass-panel p-6 rounded-xl border-l-[4px] border-l-indigo-500 hover:bg-gray-800/80 transition group cursor-pointer shadow-lg"
            >
              <div className="flex justify-between items-start mb-2">
                <h3 className="font-bold text-lg text-indigo-300">{test.test_id}: {test.scenerio || test.scenario}</h3>
                <span className="text-xs text-gray-400 bg-gray-900 border border-gray-700 px-2 py-1 rounded shadow-sm">{test.feature}</span>
              </div>
              <div className="text-sm text-gray-400 mb-4 bg-gray-900/30 p-2 rounded">
                <strong className="text-gray-300">Preconditions:</strong> {test.preconditions}
              </div>
              <div className="bg-gray-900/50 p-4 rounded-lg mb-4 text-sm font-mono text-gray-300 border border-gray-800">
                <div className="font-bold text-gray-500 mb-2 uppercase text-xs tracking-wider">Steps:</div>
                <ol className="list-decimal list-inside space-y-1 pl-2">
                  {Array.isArray(test.steps) ? test.steps.map((s, i) => <li key={i}>{s}</li>) : <li>{test.steps}</li>}
                </ol>
              </div>
              <div className="flex gap-4 text-sm border-t border-gray-700 pt-3 mt-2">
                <div className="flex-1 flex items-center gap-2">
                  <span className="text-gray-500 text-xs uppercase font-bold">Expected Result:</span>
                  <span className="text-green-400 font-medium">{test.expected_result}</span>
                </div>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </motion.div>
  );
};

const ScriptGenerator = ({ availableTests }) => {
  const [selectedTest, setSelectedTest] = useState(null);
  const [script, setScript] = useState("");
  const [loading, setLoading] = useState(false);

  // Execution state
  const [execution, setExecution] = useState(null);
  const [executing, setExecuting] = useState(false);
  const [polling, setPolling] = useState(false);

  // WebSocket integration for real-time updates
  const {
    connected: wsConnected,
    executionProgress,
    subscribeToExecution,
    unsubscribeFromExecution
  } = useExecutionSocket();

  const handleRunTest = async () => {
    if (!selectedTest) return;
    setExecuting(true);
    setExecution(null);
    try {
      // 1. Start execution
      const res = await api.post(`/agent/execute/${encodeURIComponent(selectedTest.test_id)}`);
      const executionId = res.data.execution_id;

      setExecution({ status: 'running', ...res.data });
      setPolling(true);

      // Subscribe to WebSocket updates
      subscribeToExecution(executionId);

      // 2. Poll for status (fallback for WebSocket)
      const interval = setInterval(async () => {
        try {
          const statusRes = await api.get(`/agent/executions/${executionId}`);
          setExecution(statusRes.data);
          if (statusRes.data.status !== 'running') {
            clearInterval(interval);
            setPolling(false);
            setExecuting(false);
            unsubscribeFromExecution(executionId);
          }
        } catch (err) {
          console.error('Polling error:', err);
        }
      }, 2000);
    } catch (err) {
      console.error('Execution error:', err);
      setExecuting(false);
      setPolling(false);
    }
  };

  const handleGenerateScript = async () => {
    if (!selectedTest) return;
    setLoading(true);
    setScript("");
    try {
      const res = await api.post('/agent/selenium-script', { testcase: selectedTest });
      setScript(res.data.script);
    } catch (err) {
      alert('Script generation failed: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  // Fetch script when test is selected
  useEffect(() => {
    let active = true;

    const fetchScript = async () => {
      if (!selectedTest) {
        if (active) setScript("");
        return;
      }

      if (active) {
        setLoading(true);
        // Clear previous script while loading to avoid confusion
        setScript("");
        setExecution(null);
      }

      try {
        // Correct endpoint should be /agent/selenium-scripts/{test_id}
        // Use encodeURIComponent to handle special characters in test_id
        const res = await api.get(`/agent/selenium-scripts/${encodeURIComponent(selectedTest.test_id)}`);
        if (active) {
          if (res.data.script && res.data.script.script_content) {
            setScript(res.data.script.script_content);
          } else {
            setScript("");
          }
        }
      } catch (err) {
        console.error("Failed to fetch script:", err);
        if (active) setScript("");
      } finally {
        if (active) setLoading(false);
      }
    };

    fetchScript();

    return () => {
      active = false;
    };
  }, [selectedTest]);

  const downloadScript = () => {
    const element = document.createElement("a");
    const file = new Blob([script], { type: 'text/x-python' });
    element.href = URL.createObjectURL(file);
    element.download = `test_${selectedTest.test_id || 'script'}.py`;
    document.body.appendChild(element);
    element.click();
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="p-8 h-full flex flex-col space-y-6"
    >
      <h2 className="text-3xl font-bold">Selenium Script Generator</h2>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-full min-h-0 pb-20">
        {/* Left: Test Selection */}
        <div className="lg:col-span-1 glass-panel rounded-xl flex flex-col h-full min-h-0 overflow-hidden shadow-xl">
          <div className="p-4 border-b border-gray-700 font-semibold bg-gray-800/50 backdrop-blur-md">
            Select Test Case
          </div>
          <div className="overflow-y-auto custom-scrollbar p-2 space-y-2 flex-1 bg-gray-900/30">
            {availableTests.length === 0 ? (
              <div className="p-8 text-center text-gray-500">
                No test cases generated yet. <br />Go to Test Generator tab first.
              </div>
            ) : (
              availableTests.map((test, idx) => (
                <motion.div
                  key={idx}
                  whileHover={{ scale: 1.02 }}
                  onClick={() => setSelectedTest(test)}
                  className={`p-4 rounded-lg cursor-pointer transition border border-transparent ${selectedTest === test
                    ? 'bg-indigo-600/20 border-indigo-500 shadow-[0_0_15px_rgba(99,102,241,0.2)]'
                    : 'hover:bg-gray-800 bg-gray-800/40'
                    }`}
                >
                  <div className="font-bold text-sm mb-1 text-indigo-300">{test.test_id}</div>
                  <div className="text-xs text-gray-300 line-clamp-2">{test.scenerio || test.scenario}</div>
                </motion.div>
              ))
            )}
          </div>
        </div>

        {/* Right: Preview & Code */}
        <div className="lg:col-span-2 flex flex-col gap-6 h-full min-h-0 overflow-hidden">
          {selectedTest ? (
            <>
              <div className="glass-panel p-6 rounded-xl flex-shrink-0 animate-fade-in shadow-xl">
                <h3 className="text-lg font-bold mb-2 text-indigo-300 flex items-center gap-2">
                  <TestTube size={18} /> Selected Scenario
                </h3>
                <p className="text-gray-300 bg-gray-900/50 p-3 rounded-lg border border-gray-700">{selectedTest.scenerio || selectedTest.scenario}</p>
                <button
                  onClick={handleGenerateScript}
                  disabled={loading}
                  className="mt-4 w-full bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-3 rounded-lg font-medium shadow-lg flex justify-center items-center gap-2 transition disabled:opacity-70"
                >
                  {loading ? <span className="animate-spin">⌛</span> : <Code size={18} />}
                  {script ? 'Regenerate Python Script' : 'Generate Python Script'}
                </button>
              </div>

              {/* Script Display Area */}
              {loading && !script && (
                <div className="flex flex-col items-center justify-center p-12 text-gray-500 glass-panel rounded-xl">
                  <span className="animate-spin mb-4 text-3xl">⌛</span>
                  <p>Fetching script...</p>
                </div>
              )}

              {script && (
                <motion.div
                  key={selectedTest.test_id} // Force re-render on test switch
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="glass-panel rounded-xl flex flex-col flex-1 min-h-0 overflow-hidden shadow-xl border border-gray-700"
                >
                  <div className="p-3 border-b border-gray-700 flex justify-between items-center bg-gray-800/80 backdrop-blur-sm">
                    <span className="font-mono text-xs text-green-400 bg-green-900/20 px-2 py-1 rounded">generated_script.py</span>
                    <div className="flex gap-2">
                      {/* Run Button */}
                      <button
                        onClick={handleRunTest}
                        disabled={executing || polling}
                        className={`text-white flex items-center gap-2 text-sm px-3 py-1 rounded transition ${executing ? 'bg-indigo-600/50 cursor-not-allowed' : 'bg-green-600 hover:bg-green-700'
                          }`}
                      >
                        {executing ? <span className="animate-spin">⌛</span> : <span className="font-bold">▶</span>}
                        {executing ? 'Running...' : 'Run Test'}
                      </button>

                      <button onClick={downloadScript} className="text-gray-400 hover:text-white flex items-center gap-2 text-sm bg-gray-700/50 hover:bg-gray-700 px-3 py-1 rounded transition">
                        <Download size={14} /> Download
                      </button>
                    </div>
                  </div>

                  {/* Execution Status Panel */}
                  {execution && (
                    <div className={`p-4 border-b border-gray-700 ${execution.status === 'passed' ? 'bg-green-900/20 border-green-900/50' :
                      (execution.status === 'failed' || execution.status === 'error') ? 'bg-red-900/20 border-red-900/50' :
                        'bg-blue-900/20 border-blue-900/50'
                      }`}>
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-bold text-sm uppercase flex items-center gap-2">
                          {execution.status === 'running' && <span className="animate-spin">🔄</span>}
                          {execution.status === 'passed' && <span>✅</span>}
                          {(execution.status === 'failed' || execution.status === 'error') && <span>❌</span>}
                          Status: {execution.status}
                        </span>
                        {execution.duration_seconds && (
                          <span className="text-xs text-gray-400">Duration: {execution.duration_seconds.toFixed(2)}s</span>
                        )}
                      </div>

                      {/* Real-time Progress Bar (Phase 3) */}
                      {execution.status === 'running' && executionProgress[execution.id] && (
                        <div className="mb-3">
                          <div className="flex justify-between text-xs text-gray-400 mb-1">
                            <span>{executionProgress[execution.id].message}</span>
                            <span>{executionProgress[execution.id].progress}%</span>
                          </div>
                          <div className="w-full bg-gray-700 rounded-full h-2 overflow-hidden">
                            <motion.div
                              className="bg-indigo-500 h-2 rounded-full"
                              initial={{ width: 0 }}
                              animate={{ width: `${executionProgress[execution.id].progress}%` }}
                              transition={{ duration: 0.3 }}
                            />
                          </div>
                          <div className="text-xs text-gray-500 mt-1">
                            Step {executionProgress[execution.id].step} of {executionProgress[execution.id].total}
                          </div>
                        </div>
                      )}

                      {/* Always show error message if present */}
                      {execution.error_message && (
                        <div className="mt-2 mb-2 text-sm text-red-300 font-mono bg-red-950/50 p-3 rounded border border-red-500/30 whitespace-pre-wrap">
                          <strong>Error:</strong><br />
                          {execution.error_message}
                        </div>
                      )}

                      {execution.logs && (
                        <details className="mt-2" open={execution.status === 'error' || execution.status === 'failed'}>
                          <summary className="text-xs cursor-pointer text-gray-400 hover:text-white">View Execution Logs</summary>
                          <pre className="mt-2 text-xs bg-black/50 p-2 rounded overflow-auto max-h-60 whitespace-pre-wrap font-mono text-gray-300">
                            {execution.logs}
                          </pre>
                        </details>
                      )}
                    </div>
                  )}
                  <div className="flex-1 overflow-auto custom-scrollbar" style={{ backgroundColor: '#1E1E1E' }}>
                    <SyntaxHighlighter
                      language="python"
                      style={vscDarkPlus}
                      showLineNumbers={true}
                      customStyle={{
                        margin: 0,
                        padding: '1.5rem',
                        backgroundColor: '#1E1E1E',
                        fontSize: '0.875rem',
                        lineHeight: '1.5'
                      }}
                      lineNumberStyle={{
                        minWidth: '3em',
                        paddingRight: '1em',
                        color: '#858585',
                        userSelect: 'none'
                      }}
                    >
                      {script}
                    </SyntaxHighlighter>
                  </div>
                </motion.div>
              )}
            </>
          ) : (
            <div className="h-full flex flex-col items-center justify-center text-gray-500 glass-panel rounded-xl border-dashed border-2 border-gray-700">
              <Code size={48} className="mb-4 opacity-20" />
              <p>Select a test case from the left to generate automation script.</p>
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
};




const MainApp = () => {
  const [activeTab, setActiveTab] = useState('kb');
  const [generatedTests, setGeneratedTests] = useState([]);
  const { currentProject } = useContext(ProjectContext);

  return (
    <div className="flex min-h-screen bg-gray-950 text-gray-200 font-sans selection:bg-indigo-500/30 overflow-hidden">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />

      <main className="flex-1 ml-64 p-2 h-screen overflow-hidden relative">
        {/* Background Decoration */}
        <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-indigo-600/10 rounded-full blur-[100px] pointer-events-none z-0"></div>
        <div className="absolute bottom-0 left-0 w-[500px] h-[500px] bg-purple-600/10 rounded-full blur-[100px] pointer-events-none z-0"></div>

        <div className="h-full overflow-y-auto custom-scrollbar relative z-10">
          {activeTab === 'kb' && <KnowledgeBase />}
          {activeTab === 'tests' && <TestGenerator setGeneratedTests={setGeneratedTests} />}
          {activeTab === 'scripts' && <ScriptGenerator availableTests={generatedTests} />}
          {activeTab === 'suites' && <TestSuites availableTests={generatedTests} />}
          {activeTab === 'autonomous' && <AutonomousMode />}
          {activeTab === 'results' && <ResultsTabs />}
          {activeTab === 'history' && <ExecutionHistory />}
        </div>
      </main>
    </div>
  );
};

const App = () => {
  return (
    <AuthProvider>
      <ProjectProvider>
        <AppContent />
      </ProjectProvider>
    </AuthProvider>
  );
};

const AppContent = () => {
  const { user } = useContext(AuthContext);

  if (!user) {
    return <AuthPage />;
  }

  return <MainApp />;
};

export default App;


