import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 20000,
});

export const setAuthToken = (token) => {
  if (token) {
    api.defaults.headers.common.Authorization = `Bearer ${token}`;
    try {
      localStorage.setItem('mplads_token', token);
    } catch (err) {
      /* ignore storage errors in prototype */
    }
  } else {
    delete api.defaults.headers.common.Authorization;
  }
};

try {
  const existing = localStorage.getItem('mplads_token');
  if (existing) setAuthToken(existing);
} catch (err) {
  /* ignore */
}

const ROLE_CREDENTIALS = {
  ADMIN: { username: 'admin', password: 'admin123' },
  DISTRICT_OFFICER: { username: 'district_officer', password: 'officer123' },
  AUDITOR: { username: 'auditor', password: 'auditor123' }
};

export const loginWithRole = async (role) => {
  const creds = ROLE_CREDENTIALS[role] || ROLE_CREDENTIALS.ADMIN;
  const response = await api.post('/auth/login', creds);
  setAuthToken(response.data.access_token);
  return response.data;
};

export const getCurrentUser = async () => {
  const response = await api.get('/auth/me');
  return response.data;
};

// Set active role view header
export const setApiRoleHeader = (role) => {
  api.defaults.headers.common['X-Role-View'] = role;
};

// 1. Dashboard & Risk Statistics
export const getKPIs = async () => {
  const response = await api.get('/dashboard/kpis');
  return response.data;
};

export const getTop5PercentWorks = async () => {
  const response = await api.get('/risk/top-5-percent');
  return response.data;
};

export const getRiskStatistics = async () => {
  const response = await api.get('/risk/statistics');
  return response.data;
};

// 2. Project List & Details
export const getFlaggedAnomalies = async (params = {}) => {
  const response = await api.get('/projects/anomalies', { params });
  return response.data;
};

export const getProjects = async (params = {}) => {
  const response = await api.get('/projects', { params });
  return response.data;
};

export const getProjectByCode = async (projectCode) => {
  const response = await api.get(`/projects/code/${encodeURIComponent(projectCode)}`);
  return response.data;
};

export const getProjectById = async (projectId) => {
  const response = await api.get(`/projects/${projectId}`);
  return response.data;
};

export const getProjectRiskBreakdown = async (projectId) => {
  const response = await api.get(`/projects/${projectId}/risk`);
  return response.data;
};

export const getProjectEvidence = async (projectId) => {
  const response = await api.get(`/projects/${projectId}/evidence`);
  return response.data;
};

export const getProjectMilestones = async (projectId) => {
  const response = await api.get(`/projects/${projectId}/milestones`);
  return response.data;
};

export const getProjectAuditTrail = async (projectId) => {
  const response = await api.get(`/projects/${projectId}/audit`);
  return response.data;
};

export const getProjectNotifications = async (projectId) => {
  const response = await api.get(`/projects/${projectId}/notifications`);
  return response.data;
};

export const recordProjectView = async (projectId) => {
  const response = await api.post(`/projects/${projectId}/view`, {});
  return response.data;
};

// 3. Human-in-the-Loop Case Management Actions
export const reviewProjectCase = async (projectId, payload) => {
  const response = await api.post(`/projects/${projectId}/review`, payload);
  return response.data;
};

export const requestClarification = async (projectId, payload) => {
  const response = await api.post(`/projects/${projectId}/clarification`, payload);
  return response.data;
};

export const verifyAnomaly = async (projectId, payload) => {
  const response = await api.post(`/projects/${projectId}/verify`, payload);
  return response.data;
};

export const dismissAnomaly = async (projectId, payload) => {
  const response = await api.post(`/projects/${projectId}/dismiss`, payload);
  return response.data;
};

export const resolveCase = async (projectId, payload) => {
  const response = await api.post(`/projects/${projectId}/resolve`, payload);
  return response.data;
};

export const uploadEvidence = async (projectId, payload) => {
  const response = await api.post(`/projects/${projectId}/evidence`, payload);
  return response.data;
};

// 4. Notifications
export const getNotifications = async (unreadOnly = false) => {
  const response = await api.get('/notifications', { params: { unread_only: unreadOnly } });
  return response.data;
};

export const markNotificationRead = async (notificationId) => {
  const response = await api.put(`/notifications/${notificationId}/read`);
  return response.data;
};

export const markAllNotificationsRead = async () => {
  const response = await api.post('/notifications/mark-all-read');
  return response.data;
};

// 5. ML Proposal Analyzer & LLM Report
export const analyzeProjectProposal = async (proposalData) => {
  const response = await api.post('/projects/analyze', proposalData);
  return response.data;
};

export const getProjectExplanation = async (projectId) => {
  const response = await api.get(`/projects/${projectId}/explain`);
  return response.data;
};

// 6. Database Seeder
export const seedDatabase = async () => {
  const response = await api.post('/seed');
  return response.data;
};

export default api;

