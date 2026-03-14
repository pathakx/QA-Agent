import { createContext, useState, useEffect, useContext } from 'react';
import axios from 'axios';
import { AuthContext } from './AuthContext';

export const ProjectContext = createContext();

export const ProjectProvider = ({ children }) => {
    const { user, session } = useContext(AuthContext);
    const [projects, setProjects] = useState([]);
    const [currentProject, setCurrentProject] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    // Load projects when user logs in
    useEffect(() => {
        if (user && session) {
            loadProjects();
        } else {
            // Clear projects when user logs out
            setProjects([]);
            setCurrentProject(null);
        }
    }, [user, session]);

    const loadProjects = async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await axios.get('/api/projects');
            const userProjects = response.data.projects || [];
            setProjects(userProjects);

            // Auto-select project from localStorage or first project
            const savedProjectId = localStorage.getItem('currentProjectId');
            if (savedProjectId) {
                const project = userProjects.find(p => p.id === savedProjectId);
                if (project) {
                    setCurrentProject(project);
                } else if (userProjects.length > 0) {
                    // Saved project not found, use first one
                    setCurrentProject(userProjects[0]);
                    localStorage.setItem('currentProjectId', userProjects[0].id);
                }
            } else if (userProjects.length > 0) {
                // No saved project, use first one
                setCurrentProject(userProjects[0]);
                localStorage.setItem('currentProjectId', userProjects[0].id);
            }
        } catch (err) {
            console.error('Failed to load projects:', err);
            setError(err.response?.data?.detail || 'Failed to load projects');
        } finally {
            setLoading(false);
        }
    };

    const createProject = async (name, description = '') => {
        setLoading(true);
        setError(null);
        try {
            const response = await axios.post('/api/projects', {
                name,
                description
            });
            const newProject = response.data;

            // Add to projects list
            setProjects(prev => [newProject, ...prev]);

            // Set as current project
            setCurrentProject(newProject);
            localStorage.setItem('currentProjectId', newProject.id);

            return newProject;
        } catch (err) {
            console.error('Failed to create project:', err);
            setError(err.response?.data?.detail || 'Failed to create project');
            throw err;
        } finally {
            setLoading(false);
        }
    };

    const switchProject = (project) => {
        setCurrentProject(project);
        localStorage.setItem('currentProjectId', project.id);
    };

    const updateProject = async (projectId, updates) => {
        setLoading(true);
        setError(null);
        try {
            const response = await axios.put(`/api/projects/${projectId}`, updates);
            const updatedProject = response.data.project;

            // Update in projects list
            setProjects(prev => prev.map(p =>
                p.id === projectId ? updatedProject : p
            ));

            // Update current project if it's the one being updated
            if (currentProject?.id === projectId) {
                setCurrentProject(updatedProject);
            }

            return updatedProject;
        } catch (err) {
            console.error('Failed to update project:', err);
            setError(err.response?.data?.detail || 'Failed to update project');
            throw err;
        } finally {
            setLoading(false);
        }
    };

    const deleteProject = async (projectId) => {
        setLoading(true);
        setError(null);
        try {
            await axios.delete(`/api/projects/${projectId}`);

            // Remove from projects list
            setProjects(prev => prev.filter(p => p.id !== projectId));

            // If deleted project was current, switch to first available
            if (currentProject?.id === projectId) {
                const remainingProjects = projects.filter(p => p.id !== projectId);
                if (remainingProjects.length > 0) {
                    setCurrentProject(remainingProjects[0]);
                    localStorage.setItem('currentProjectId', remainingProjects[0].id);
                } else {
                    setCurrentProject(null);
                    localStorage.removeItem('currentProjectId');
                }
            }
        } catch (err) {
            console.error('Failed to delete project:', err);
            setError(err.response?.data?.detail || 'Failed to delete project');
            throw err;
        } finally {
            setLoading(false);
        }
    };

    const getProjectStats = async (projectId) => {
        try {
            const response = await axios.get(`/api/projects/${projectId}/stats`);
            return response.data;
        } catch (err) {
            console.error('Failed to get project stats:', err);
            throw err;
        }
    };

    const value = {
        projects,
        currentProject,
        loading,
        error,
        createProject,
        switchProject,
        updateProject,
        deleteProject,
        refreshProjects: loadProjects,
        getProjectStats
    };

    return (
        <ProjectContext.Provider value={value}>
            {children}
        </ProjectContext.Provider>
    );
};
