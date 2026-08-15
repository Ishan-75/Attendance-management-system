import apiClient from './axios';

export const holidayApi = {
  getHolidays: async (year = null, activeOnly = false) => {
    const params = {};
    if (year) params.year = year;
    if (activeOnly) params.active_only = activeOnly;
    const res = await apiClient.get('/holidays', { params });
    return res.data;
  },
  createHoliday: async (data) => {
    const res = await apiClient.post('/holidays', data);
    return res.data;
  },
  updateHoliday: async (id, data) => {
    const res = await apiClient.put(`/holidays/${id}`, data);
    return res.data;
  },
  deleteHoliday: async (id) => {
    const res = await apiClient.delete(`/holidays/${id}`);
    return res.data;
  },
};
