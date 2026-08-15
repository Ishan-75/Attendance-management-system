import apiClient from './axios';

export const systemApi = {
  getSmtpStatus: async () => {
    const res = await apiClient.get('/system/smtp-status');
    return res.data;
  },

  testEmail: async (targetEmail = 'attendancesystem55@gmail.com') => {
    const res = await apiClient.post('/system/test-email', {
      target_email: targetEmail,
    });
    return res.data;
  },
};
