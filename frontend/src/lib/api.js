import axios from 'axios';

// Create a centralized axios instance
export const api = axios.create({
    baseURL: import.meta.env.DEV ? 'http://localhost:8001/api' : '/api'
});

// Add a request interceptor to dynamically inject the project ID from localStorage
// This avoids React lifecycle race conditions where the context might update after the request fires
api.interceptors.request.use((config) => {
    const projectId = localStorage.getItem('currentProjectId');
    if (projectId) {
        config.headers['project-id'] = projectId;
    }
    return config;
}, (error) => {
    return Promise.reject(error);
});
