import apiClient from './axios';

export const dashboardApi = {
  getData: async (dateStr = null) => {
    const params = dateStr ? { date: dateStr } : {};
    const res = await apiClient.get('/dashboard/data', { params });
    return res.data;
  },
};
