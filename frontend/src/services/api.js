import axios from 'axios';

// Create an Axios instance
const api = axios.create({
  baseURL: 'http://localhost:8029/api',
});

// Automatically attach session ID to every request
api.interceptors.request.use(
  (config) => {
    const sessionId = localStorage.getItem('sessionId');
    if (sessionId) {
      config.headers['Session-ID'] = sessionId;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

export default api;
