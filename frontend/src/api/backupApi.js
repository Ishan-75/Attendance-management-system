import apiClient from './axios';

export const backupApi = {
  getBackups: async () => {
    const res = await apiClient.get('/backups');
    return res.data;
  },
  createBackup: async () => {
    const res = await apiClient.post('/backups');
    return res.data;
  },
  getDownloadUrl: (backupId) => {
    const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';
    return `${baseUrl}/backups/${backupId}/download`;
  },
  restoreBackup: async (backupId, confirm = true) => {
    const res = await apiClient.post(`/backups/${backupId}/restore`, { backup_id: backupId, confirm });
    return res.data;
  },
};
