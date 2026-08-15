import apiClient from './axios';

export const authApi = {
  login: async (username_or_email, password) => {
    const res = await apiClient.post('/auth/login', { username_or_email, password });
    return res.data;
  },
  getMe: async () => {
    const res = await apiClient.get('/auth/me');
    return res.data;
  },
  verifyEmail: async (token) => {
    const res = await apiClient.post('/auth/verify-email', { token });
    return res.data;
  },
  forgotPassword: async (email) => {
    const res = await apiClient.post('/auth/forgot-password', { email });
    return res.data;
  },
  resetPassword: async (token, new_password) => {
    const res = await apiClient.post('/auth/reset-password', { token, new_password });
    return res.data;
  },
  changePassword: async (current_password, new_password) => {
    const res = await apiClient.post('/auth/change-password', { current_password, new_password });
    return res.data;
  },
  logout: async () => {
    try {
      await apiClient.post('/auth/logout');
    } catch (e) {
      // Ignore errors on logout
    }
  }
};
