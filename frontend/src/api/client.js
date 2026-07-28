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

export const getDatabaseStats = async () => {
  const res = await api.get('/database/stats');
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

export const getDocuments = async () => {
  const res = await api.get('/documents');
  return res.data;
};

export const processFullPipeline = async (fileId) => {
  const res = await api.post(`/documents/${fileId}/process-full-pipeline`);
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

export const searchSemantic = async (query, topK = 5) => {
  const res = await api.get(`/search/semantic?query=${encodeURIComponent(query)}&top_k=${topK}`);
  return res.data;
};

export const retrieveContext = async (question, topK = 3, maxChars = 4000) => {
  const res = await api.post('/retrieval/context', {
    question,
    top_k: topK,
    max_chars: maxChars,
  });
  return res.data;
};

export const askQuestion = async (question, topK = 3, maxChars = 4000) => {
  const res = await api.post('/qa/ask', {
    question,
    top_k: topK,
    max_chars: maxChars,
  });
  return res.data;
};

export default api;
