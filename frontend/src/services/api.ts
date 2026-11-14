import axios from 'axios';
import {
  User,
  Server,
  ServerRegisterToken,
  MetricPoint,
  ServerDetailedMetrics,
  Alert,
  AnomalyLog,
  ModelStatus,
  Recommendation,
  OverviewStats
} from '../types';

const api = axios.create({
  baseURL: '/api'
});

// Attach JWT access token automatically
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('cp_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 Unauthorized redirects
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      if (!window.location.pathname.includes('/login') && !window.location.pathname.includes('/register')) {
        localStorage.removeItem('cp_token');
        localStorage.removeItem('cp_user');
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export const authApi = {
  login: async (email: string, password: string) => {
    const res = await api.post('/auth/login', { email, password });
    return res.data;
  },
  register: async (email: string, password: string, fullName: string, orgName: string) => {
    const res = await api.post('/auth/register', {
      email,
      password,
      full_name: fullName,
      organization_name: orgName
    });
    return res.data;
  },
  getMe: async (): Promise<User> => {
    const res = await api.get('/auth/me');
    return res.data;
  },
  logout: () => {
    localStorage.removeItem('cp_token');
    localStorage.removeItem('cp_user');
  }
};

export const serverApi = {
  getServers: async (status?: string, search?: string): Promise<Server[]> => {
    const params: any = {};
    if (status) params.status = status;
    if (search) params.search = search;
    const res = await api.get('/servers', { params });
    return res.data;
  },
  createServer: async (name: string, description?: string): Promise<ServerRegisterToken> => {
    const res = await api.post('/servers', { name, description });
    return res.data;
  },
  getServer: async (serverId: string): Promise<Server> => {
    const res = await api.get(`/servers/${serverId}`);
    return res.data;
  },
  updateServer: async (serverId: string, data: { name?: string; description?: string }): Promise<Server> => {
    const res = await api.put(`/servers/${serverId}`, data);
    return res.data;
  },
  deleteServer: async (serverId: string) => {
    const res = await api.delete(`/servers/${serverId}`);
    return res.data;
  }
};

export const metricsApi = {
  getLatest: async () => {
    const res = await api.get('/metrics/latest');
    return res.data;
  },
  getHistory: async (serverId: string, hours: number = 1): Promise<MetricPoint[]> => {
    const res = await api.get('/metrics/history', { params: { server_id: serverId, hours } });
    return res.data;
  },
  getServerDetailedMetrics: async (serverId: string): Promise<ServerDetailedMetrics> => {
    const res = await api.get(`/metrics/${serverId}`);
    return res.data;
  }
};

export const alertsApi = {
  getAlerts: async (status: string = 'active', severity?: string, serverId?: string): Promise<Alert[]> => {
    const params: any = { status };
    if (severity) params.severity = severity;
    if (serverId) params.server_id = serverId;
    const res = await api.get('/alerts', { params });
    return res.data;
  },
  acknowledge: async (alertId: string, byName?: string): Promise<Alert> => {
    const res = await api.put(`/alerts/${alertId}/acknowledge`, { acknowledged_by: byName });
    return res.data;
  },
  resolve: async (alertId: string, byName?: string): Promise<Alert> => {
    const res = await api.put(`/alerts/${alertId}/resolve`, { resolved_by: byName });
    return res.data;
  }
};

export const analyticsApi = {
  getOverview: async (): Promise<OverviewStats> => {
    const res = await api.get('/analytics/overview');
    return res.data;
  },
  getCpu: async () => {
    const res = await api.get('/analytics/cpu');
    return res.data;
  },
  getMemory: async () => {
    const res = await api.get('/analytics/memory');
    return res.data;
  },
  getDisk: async () => {
    const res = await api.get('/analytics/disk');
    return res.data;
  },
  getNetwork: async () => {
    const res = await api.get('/analytics/network');
    return res.data;
  }
};

export const aiApi = {
  getAnomalies: async (serverId?: string): Promise<AnomalyLog[]> => {
    const params: any = {};
    if (serverId) params.server_id = serverId;
    const res = await api.get('/ai/anomalies', { params });
    return res.data;
  },
  train: async (contamination: number = 0.05) => {
    const res = await api.post(`/ai/train?contamination=${contamination}`);
    return res.data;
  },
  getModelStatus: async (): Promise<ModelStatus> => {
    const res = await api.get('/ai/model-status');
    return res.data;
  },
  getRecommendations: async (serverId?: string): Promise<Recommendation[]> => {
    const params: any = {};
    if (serverId) params.server_id = serverId;
    const res = await api.get('/ai/recommendations', { params });
    return res.data;
  }
};

export const profilerApi = {
  profileServer: async (serverId: string) => {
    const res = await api.get(`/profiler/server/${serverId}`);
    return res.data;
  }
};

export const reportsApi = {
  getDaily: async () => {
    const res = await api.get('/reports/daily');
    return res.data;
  },
  getWeekly: async () => {
    const res = await api.get('/reports/weekly');
    return res.data;
  },
  downloadExport: (format: 'csv' | 'pdf', days: number = 7) => {
    window.open(`/api/reports/export?format=${format}&days=${days}`, '_blank');
  }
};

export default api;
