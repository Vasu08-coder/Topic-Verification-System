import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor: attach Bearer token for admin and student endpoints
apiClient.interceptors.request.use(
  (config) => {
    if (config.url && config.url.startsWith('/api/admin')) {
      const adminToken = sessionStorage.getItem('admin_token');
      if (adminToken) {
        config.headers.Authorization = `Bearer ${adminToken}`;
      }
    } else if (config.url && (config.url.startsWith('/api/submissions') || config.url.startsWith('/api/students'))) {
      const studentToken = sessionStorage.getItem('student_token');
      if (studentToken) {
        config.headers.Authorization = `Bearer ${studentToken}`;
      }
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor: on 401, clear appropriate session and redirect
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401 && error.config && error.config.url) {
      if (error.config.url.startsWith('/api/admin')) {
        sessionStorage.removeItem('admin_token');
        sessionStorage.removeItem('admin_name');
        sessionStorage.removeItem('user_type');
        if (window.location.pathname !== '/admin/login') {
          window.location.href = '/admin/login';
        }
      } else if (error.config.url.startsWith('/api/submissions') || error.config.url.startsWith('/api/students')) {
        sessionStorage.removeItem('student_token');
        sessionStorage.removeItem('student_data');
        sessionStorage.removeItem('user_type');
        if (window.location.pathname !== '/student/login') {
          window.location.href = '/student/login';
        }
      }
    }
    return Promise.reject(error);
  }
);

// Helper function to build query strings, omitting empty/undefined/null values
const buildQueryString = (params = {}) => {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      query.append(key, value);
    }
  });
  const str = query.toString();
  return str ? `?${str}` : '';
};

// API Functions
// Student Auth Functions
export const studentRegister = async (sisId, fullName, branch, password) => {
  const response = await apiClient.post('/api/students/register', {
    sis_id: sisId,
    full_name: fullName,
    branch,
    password,
  });
  return response.data;
};

export const studentLogin = async (sisId, password) => {
  const response = await apiClient.post('/api/students/login', {
    sis_id: sisId,
    password,
  });
  return response.data;
};

// Student Submission Functions (auth required)
export const checkSimilarity = async (data) => {
  const response = await apiClient.post('/api/submissions/check-similarity', data);
  return response.data;
};

export const getSubmissionStatus = async (submissionId) => {
  const response = await apiClient.get(`/api/submissions/${submissionId}/status`);
  return response.data;
};

export const uploadAbstract = async (submissionId, file) => {
  const formData = new FormData();
  formData.append('file', file);
  const response = await apiClient.post(`/api/submissions/${submissionId}/upload-abstract`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

// Public Archive (no auth required)
export const getPublicArchive = async (moduleType, filters = {}) => {
  const queryString = buildQueryString(filters);
  const response = await apiClient.get(`/api/public/archive/${moduleType}${queryString}`);
  return response.data;
};

// Admin Functions (auth required)
export const adminLogin = async (username, password) => {
  const response = await apiClient.post('/api/auth/login', { username, password });
  return response.data;
};

export const getAdminSubmissions = async (filters = {}) => {
  const queryString = buildQueryString(filters);
  const response = await apiClient.get(`/api/admin/submissions${queryString}`);
  return response.data;
};

export const getAdminSubmissionDetail = async (submissionId) => {
  const response = await apiClient.get(`/api/admin/submissions/${submissionId}`);
  return response.data;
};

export const submitDecision = async (submissionId, action, notes) => {
  const response = await apiClient.post(`/api/admin/submissions/${submissionId}/decision`, {
    action,
    notes,
  });
  return response.data;
};

export const getDashboardStats = async () => {
  const response = await apiClient.get('/api/admin/submissions/dashboard-stats');
  return response.data;
};

export const getArchive = async (moduleType, filters = {}) => {
  const queryString = buildQueryString(filters);
  const response = await apiClient.get(`/api/admin/archive/${moduleType}${queryString}`);
  return response.data;
};

export const downloadSubmissionDocument = async (submissionId) => {
  // Use blob response type to handle binary file data
  const response = await apiClient.get(`/api/admin/submissions/${submissionId}/document`, {
    responseType: 'blob',
  });
  return response;
};

export const importRecords = async (moduleType, file) => {
  const formData = new FormData();
  formData.append('file', file);
  const response = await apiClient.post(`/api/admin/import/${moduleType}`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

export const exportRecords = (moduleType, filters = {}) => {
  const queryString = buildQueryString(filters);
  return `${API_BASE_URL}/api/admin/export/${moduleType}${queryString}`;
};

export default apiClient;