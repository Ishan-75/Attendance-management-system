import apiClient from './axios';

export const auditApi = {
  getAuditLogs: async (params = {}) => {
    const res = await apiClient.get('/audit-logs', { params });
    return res.data;
  },
};
