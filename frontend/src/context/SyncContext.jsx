import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { syncApi } from '../api/syncApi';
import { offlineDb } from '../utils/offlineDb';
import { useToast } from './ToastContext';
import { useAuth } from './AuthContext';

const SyncContext = createContext(null);

const getDeviceId = () => {
  let id = localStorage.getItem('app_device_id');
  if (!id) {
    id = `dev_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`;
    localStorage.setItem('app_device_id', id);
  }
  return id;
};

export const SyncProvider = ({ children }) => {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [isSyncing, setIsSyncing] = useState(false);
  const [pendingCount, setPendingCount] = useState(0);
  const [conflictsCount, setConflictsCount] = useState(0);
  const [lastSyncTime, setLastSyncTime] = useState(() => localStorage.getItem('last_sync_time') || null);

  const deviceId = getDeviceId();
  const toast = useToast();
  const { isAuthenticated, user } = useAuth();

  // Refresh count of pending offline operations
  const refreshPendingCount = useCallback(async () => {
    try {
      const queue = await offlineDb.getPendingQueue();
      setPendingCount(queue.length);
    } catch (e) {
      // ignore
    }
  }, []);

  // Check pending conflicts
  const refreshConflictsCount = useCallback(async () => {
    if (!isAuthenticated || !navigator.onLine) return;
    try {
      const res = await syncApi.getConflicts();
      if (res.success && Array.isArray(res.data)) {
        setConflictsCount(res.data.length);
      }
    } catch (e) {
      // ignore
    }
  }, [isAuthenticated]);

  // Main synchronization engine
  const syncNow = useCallback(async (silent = false) => {
    if (!navigator.onLine || !isAuthenticated) return;
    setIsSyncing(true);

    try {
      // 1. Heartbeat device
      await syncApi.registerDevice({
        device_id: deviceId,
        device_name: `${user?.full_name || 'User'} Device (${navigator.platform || 'Web'})`,
        platform: 'web',
        app_version: '1.0.0',
      });

      // 2. Push pending offline operations from IndexedDB
      const pendingQueue = await offlineDb.getPendingQueue();
      if (pendingQueue.length > 0) {
        const pushRes = await syncApi.pushSync(deviceId, pendingQueue);
        if (pushRes.success) {
          // Clear synced items
          await offlineDb.clearQueue();
          await refreshPendingCount();
          if (!silent) {
            toast.success(`Synced ${pushRes.data.processed} offline changes`);
          }
        }
      }

      // 3. Pull latest delta master records from server and store in IndexedDB
      const pullRes = await syncApi.pullSync(lastSyncTime);
      if (pullRes.success && pullRes.data) {
        await offlineDb.cacheMasterData(pullRes.data);
        const newSyncTime = pullRes.data.timestamp || new Date().toISOString();
        setLastSyncTime(newSyncTime);
        localStorage.setItem('last_sync_time', newSyncTime);
      }

      // 4. Update conflicts count
      await refreshConflictsCount();

      if (!silent && pendingQueue.length === 0) {
        toast.info('All data is synchronized with central database');
      }
    } catch (err) {
      if (!silent) {
        toast.error('Sync failed. Please check network connection.');
      }
    } finally {
      setIsSyncing(false);
    }
  }, [deviceId, isAuthenticated, user, lastSyncTime, refreshPendingCount, refreshConflictsCount, toast]);

  // Queue an offline operation (with instant push if currently online)
  const queueChange = useCallback(async (entityType, entityId, operation, payload) => {
    try {
      await offlineDb.enqueueOperation({
        entity_type: entityType,
        entity_id: entityId,
        operation: operation,
        payload: payload,
      });
      await refreshPendingCount();

      if (navigator.onLine && isAuthenticated) {
        // Trigger non-blocking push
        syncNow(true);
      } else {
        toast.warning('Working offline: Change saved locally and queued for sync.');
      }
    } catch (err) {
      toast.error('Failed to write offline change to local database');
    }
  }, [isAuthenticated, refreshPendingCount, syncNow, toast]);

  // Listen to network status changes
  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true);
      toast.success('Internet connection restored. Starting auto-sync...');
      syncNow(true);
    };

    const handleOffline = () => {
      setIsOnline(false);
      toast.warning('You are currently offline. Operations will be stored in local SQLite/IndexedDB.');
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    refreshPendingCount();

    // Auto-sync on initial login
    if (navigator.onLine && isAuthenticated) {
      syncNow(true);
    }

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [isAuthenticated]);

  return (
    <SyncContext.Provider
      value={{
        isOnline,
        isSyncing,
        pendingCount,
        conflictsCount,
        lastSyncTime,
        deviceId,
        syncNow,
        queueChange,
        refreshPendingCount,
        refreshConflictsCount,
      }}
    >
      {children}
    </SyncContext.Provider>
  );
};

export const useSync = () => {
  const context = useContext(SyncContext);
  if (!context) {
    throw new Error('useSync must be used within a SyncProvider');
  }
  return context;
};
