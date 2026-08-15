import apiClient from './axios';

export const syncApi = {
  pushSync: async (deviceId, operations) => {
    const res = await apiClient.post('/sync/push', {
      device_id: deviceId,
      operations: operations,
    });
    return res.data;
  },

  pullSync: async (since = null) => {
    const res = await apiClient.get('/sync/pull', {
      params: since ? { since } : {},
    });
    return res.data;
  },

  getConflicts: async () => {
    const res = await apiClient.get('/sync/conflicts');
    return res.data;
  },

  resolveConflict: async (conflictId, resolutionStrategy, resolutionNotes = '') => {
    const res = await apiClient.post(`/sync/conflicts/${conflictId}/resolve`, {
      resolution_strategy: resolutionStrategy,
      resolution_notes: resolutionNotes,
    });
    return res.data;
  },

  registerDevice: async (deviceData) => {
    const res = await apiClient.post('/devices/register', deviceData);
    return res.data;
  },

  getDevices: async () => {
    const res = await apiClient.get('/devices');
    return res.data;
  },
};
