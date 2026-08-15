import apiClient from './axios';

export const userApi = {
  getUsers: async () => {
    const res = await apiClient.get('/users');
    return res.data;
  },
  createUser: async (data) => {
    const res = await apiClient.post('/users', data);
    return res.data;
  },
  updateUser: async (id, data) => {
    const res = await apiClient.put(`/users/${id}`, data);
    return res.data;
  },
};
