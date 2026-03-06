import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const login = (email, password) =>
  api.post('/auth/login', { email, password });

export const register = (email, username, password) =>
  api.post('/auth/register', { email, username, password });

export const getMe = () => api.get('/auth/me');

export const analyzeGame = (pgn) => api.post('/analyze/game', { pgn });

export const analyzePosition = (fen) => api.post('/analyze/position', { fen });

export const getHistory = () => api.get('/analyze/history');

export const saveGame = (gameData) =>
  api.post('/analyze/save', {
    pgn: gameData.pgn,
    result: gameData.analysis?.result ?? null,
    analysis_json: gameData.analysis ? JSON.stringify(gameData.analysis) : null,
  });

export const getProfile = () => api.get('/player/profile');

export const classifyPlayer = () => api.post('/player/classify');

export default api;
