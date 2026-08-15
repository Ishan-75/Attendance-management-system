import apiClient from './axios';

export const settingApi = {
  getSettings: async () => {
    const res = await apiClient.get('/settings');
    return res.data;
  },
  updateSettings: async (settingsList) => {
    const res = await apiClient.put('/settings', { settings: settingsList });
    return res.data;
  },
};
