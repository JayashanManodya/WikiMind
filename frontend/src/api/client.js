import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

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
