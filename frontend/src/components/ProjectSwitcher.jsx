import { useContext, useState } from 'react';
import { ProjectContext } from '../contexts/ProjectContext';
import { FolderOpen, Plus, Pencil, Trash2, Check, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export const ProjectSwitcher = () => {
    const {
        projects,
        currentProject,
        switchProject,
        createProject,
        updateProject,
        deleteProject,
        loading
    } = useContext(ProjectContext);

    const [showCreate, setShowCreate] = useState(false);
    const [newName, setNewName] = useState('');
    const [newDescription, setNewDescription] = useState('');
    const [editingId, setEditingId] = useState(null);
    const [editName, setEditName] = useState('');
    const [editDescription, setEditDescription] = useState('');

    const handleCreate = async () => {
        if (!newName.trim()) return;

        try {
            await createProject(newName, newDescription);
            setNewName('');
            setNewDescription('');
            setShowCreate(false);
        } catch (error) {
            alert('Failed to create project: ' + error.message);
        }
    };

    const startEdit = (project) => {
        setEditingId(project.id);
        setEditName(project.name);
        setEditDescription(project.description || '');
    };

    const handleUpdate = async (projectId) => {
        try {
            await updateProject(projectId, {
                name: editName,
                description: editDescription
            });
            setEditingId(null);
        } catch (error) {
            alert('Failed to update project: ' + error.message);
        }
    };

    const handleDelete = async (projectId, projectName) => {
        if (!confirm(`Are you sure you want to delete "${projectName}"? This cannot be undone.`)) {
            return;
        }

        try {
            await deleteProject(projectId);
        } catch (error) {
            alert('Failed to delete project: ' + error.message);
        }
    };

    return (
        <div className="p-4 border-b border-gray-800 bg-gray-900/50">
            <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                    <FolderOpen size={16} className="text-indigo-400" />
                    <span className="text-xs text-gray-500 uppercase font-bold">Current Project</span>
                </div>
                <button
                    onClick={() => setShowCreate(!showCreate)}
                    className="text-indigo-400 hover:text-indigo-300 transition p-1 rounded hover:bg-indigo-500/10"
                    title="Create new project"
                >
                    <Plus size={18} />
                </button>
            </div>

            {/* Create New Project Form */}
            <AnimatePresence>
                {showCreate && (
                    <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        className="mb-3 space-y-2"
                    >
                        <input
                            type="text"
                            value={newName}
                            onChange={(e) => setNewName(e.target.value)}
                            placeholder="Project name *"
                            className="w-full p-2 rounded bg-gray-800 border border-gray-700 text-sm text-white placeholder-gray-500 focus:border-indigo-500 focus:outline-none"
                            onKeyDown={(e) => e.key === 'Enter' && handleCreate()}
                            autoFocus
                        />
                        <input
                            type="text"
                            value={newDescription}
                            onChange={(e) => setNewDescription(e.target.value)}
                            placeholder="Description (optional)"
                            className="w-full p-2 rounded bg-gray-800 border border-gray-700 text-sm text-white placeholder-gray-500 focus:border-indigo-500 focus:outline-none"
                            onKeyDown={(e) => e.key === 'Enter' && handleCreate()}
                        />
                        <div className="flex gap-2">
                            <button
                                onClick={handleCreate}
                                disabled={!newName.trim() || loading}
                                className="flex-1 bg-indigo-600 hover:bg-indigo-700 text-white px-3 py-2 rounded text-sm font-medium transition disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                Create
                            </button>
                            <button
                                onClick={() => {
                                    setShowCreate(false);
                                    setNewName('');
                                    setNewDescription('');
                                }}
                                className="px-3 py-2 rounded text-sm text-gray-400 hover:text-white hover:bg-gray-800 transition"
                            >
                                Cancel
                            </button>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Project List */}
            {projects.length === 0 ? (
                <div className="text-center text-gray-500 text-sm py-4">
                    No projects yet. Create one to get started!
                </div>
            ) : (
                <div className="space-y-1 max-h-60 overflow-y-auto custom-scrollbar">
                    {projects.map(project => (
                        <div
                            key={project.id}
                            className={`p-2 rounded-lg cursor-pointer transition border ${currentProject?.id === project.id
                                    ? 'bg-indigo-600/20 border-indigo-500/30 text-indigo-300'
                                    : 'border-transparent hover:bg-gray-800 text-gray-300 hover:text-white'
                                }`}
                        >
                            {editingId === project.id ? (
                                // Edit Mode
                                <div className="space-y-2">
                                    <input
                                        type="text"
                                        value={editName}
                                        onChange={(e) => setEditName(e.target.value)}
                                        className="w-full p-1 rounded bg-gray-800 border border-gray-700 text-sm text-white"
                                        autoFocus
                                    />
                                    <input
                                        type="text"
                                        value={editDescription}
                                        onChange={(e) => setEditDescription(e.target.value)}
                                        placeholder="Description"
                                        className="w-full p-1 rounded bg-gray-800 border border-gray-700 text-sm text-white"
                                    />
                                    <div className="flex gap-1">
                                        <button
                                            onClick={() => handleUpdate(project.id)}
                                            className="flex-1 bg-green-600 hover:bg-green-700 text-white px-2 py-1 rounded text-xs flex items-center justify-center gap-1"
                                        >
                                            <Check size={14} /> Save
                                        </button>
                                        <button
                                            onClick={() => setEditingId(null)}
                                            className="px-2 py-1 rounded text-xs text-gray-400 hover:text-white hover:bg-gray-700 flex items-center gap-1"
                                        >
                                            <X size={14} /> Cancel
                                        </button>
                                    </div>
                                </div>
                            ) : (
                                // View Mode
                                <div className="flex items-center justify-between group">
                                    <div
                                        className="flex-1 min-w-0"
                                        onClick={() => switchProject(project)}
                                    >
                                        <div className="font-medium text-sm truncate">
                                            {project.name}
                                        </div>
                                        {project.description && (
                                            <div className="text-xs text-gray-500 truncate">
                                                {project.description}
                                            </div>
                                        )}
                                    </div>
                                    <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition ml-2">
                                        <button
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                startEdit(project);
                                            }}
                                            className="p-1 rounded hover:bg-gray-700 text-gray-400 hover:text-yellow-400"
                                            title="Edit project"
                                        >
                                            <Pencil size={14} />
                                        </button>
                                        <button
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                handleDelete(project.id, project.name);
                                            }}
                                            className="p-1 rounded hover:bg-gray-700 text-gray-400 hover:text-red-400"
                                            title="Delete project"
                                        >
                                            <Trash2 size={14} />
                                        </button>
                                    </div>
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};
