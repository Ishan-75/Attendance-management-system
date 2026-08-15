import apiClient from './axios';

export const departmentApi = {
  getDepartments: async (activeOnly = false) => {
    const res = await apiClient.get('/departments', { params: { active_only: activeOnly } });
    return res.data;
  },
  createDepartment: async (data) => {
    const res = await apiClient.post('/departments', data);
    return res.data;
  },
  updateDepartment: async (id, data) => {
    const res = await apiClient.put(`/departments/${id}`, data);
    return res.data;
  },
  deleteDepartment: async (id) => {
    const res = await apiClient.delete(`/departments/${id}`);
    return res.data;
  },
};
