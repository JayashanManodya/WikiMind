import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor to attach Authorization Bearer token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('wikimind_token') || localStorage.getItem('wikillm_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, (error) => {
  return Promise.reject(error);
});

export const loginWithGoogle = async (credential) => {
  const res = await api.post('/auth/google', { credential });
  return res.data;
};

export const getCurrentUser = async () => {
  const res = await api.get('/auth/me');
  return res.data;
};

export const getHealth = async () => {
  const res = await api.get('/health');
  return res.data;
};

export const uploadDocument = async (file, autoProcess = true) => {
  const formData = new FormData();
  formData.append('file', file);

  const res = await api.post(`/upload?auto_process=${autoProcess}`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return res.data;
};

export const getWikiIndex = async () => {
  const res = await api.get('/wiki/index');
  return res.data;
};

export const getWikiPage = async (entityName) => {
  const res = await api.get(`/wiki/page/${encodeURIComponent(entityName)}`);
  return res.data;
};

export const getWikiGraph = async () => {
  const res = await api.get('/wiki/graph');
  return res.data;
};

export const askQuestion = async (question) => {
  const res = await api.post('/qa/ask', {
    question
  });
  return res.data;
};

export default api;
