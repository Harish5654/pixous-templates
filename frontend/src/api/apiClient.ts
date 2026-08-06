import axios from 'axios';
import { useAuthStore } from '../store/authStore';

// VITE_API_URL is the backend's origin only (no path). Leave it unset for a
// same-origin single-service deploy (frontend served by the backend itself);
// set it to the backend's own URL when the two are deployed as separate
// services. All API routes live under /api regardless.
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:9090';

export const apiClient = axios.create({
  baseURL: `${API_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().logout();
    }
    return Promise.reject(error);
  }
);
