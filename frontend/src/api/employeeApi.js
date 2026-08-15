import apiClient from './axios';

export const employeeApi = {
  getEmployees: async (params = {}) => {
    const res = await apiClient.get('/employees', { params });
    return res.data;
  },
  getEmployee: async (id) => {
    const res = await apiClient.get(`/employees/${id}`);
    return res.data;
  },
  createEmployee: async (data) => {
    const res = await apiClient.post('/employees', data);
    return res.data;
  },
  updateEmployee: async (id, data) => {
    const res = await apiClient.put(`/employees/${id}`, data);
    return res.data;
  },
  updateStatus: async (id, status, reason = '') => {
    const res = await apiClient.patch(`/employees/${id}/status`, { status, reason });
    return res.data;
  },
  deleteEmployee: async (id) => {
    const res = await apiClient.delete(`/employees/${id}`);
    return res.data;
  },
};
