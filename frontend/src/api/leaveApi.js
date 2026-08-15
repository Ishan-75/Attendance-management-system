import apiClient from './axios';

export const leaveApi = {
  getLeaves: async (params = {}) => {
    const res = await apiClient.get('/leaves', { params });
    return res.data;
  },
  applyLeave: async (data) => {
    const res = await apiClient.post('/leaves', data);
    return res.data;
  },
  approveLeave: async (id, reason = '') => {
    const res = await apiClient.patch(`/leaves/${id}/approve`, { reason });
    return res.data;
  },
  rejectLeave: async (id, reason) => {
    const res = await apiClient.patch(`/leaves/${id}/reject`, { reason });
    return res.data;
  },
};
