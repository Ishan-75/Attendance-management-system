/**
 * Offline-First IndexedDB Local Storage Layer
 * Manages local cache for employees, departments, holidays, attendance, leaves, and the sync queue.
 */

const DB_NAME = 'WorkforceHubDB';
const DB_VERSION = 1;

export const openOfflineDB = () => {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);

    request.onupgradeneeded = (event) => {
      const db = event.target.result;
      
      // Store for pending synchronization operations
      if (!db.objectStoreNames.contains('sync_queue')) {
        const syncStore = db.createObjectStore('sync_queue', { keyPath: 'operation_id' });
        syncStore.createIndex('status', 'status', { unique: false });
        syncStore.createIndex('created_at', 'created_at', { unique: false });
      }

      // Cached entities
      if (!db.objectStoreNames.contains('employees')) {
        db.createObjectStore('employees', { keyPath: 'id' });
      }
      if (!db.objectStoreNames.contains('departments')) {
        db.createObjectStore('departments', { keyPath: 'id' });
      }
      if (!db.objectStoreNames.contains('holidays')) {
        db.createObjectStore('holidays', { keyPath: 'id' });
      }
      if (!db.objectStoreNames.contains('attendance')) {
        const attStore = db.createObjectStore('attendance', { keyPath: 'id', autoIncrement: true });
        attStore.createIndex('employee_date', ['employee_id', 'attendance_date'], { unique: false });
      }
      if (!db.objectStoreNames.contains('leaves')) {
        db.createObjectStore('leaves', { keyPath: 'id', autoIncrement: true });
      }
    };

    request.onsuccess = (event) => resolve(event.target.result);
    request.onerror = (event) => reject(event.target.error);
  });
};

export const offlineDb = {
  // Sync Queue Operations
  enqueueOperation: async (op) => {
    const db = await openOfflineDB();
    return new Promise((resolve, reject) => {
      const tx = db.transaction('sync_queue', 'readwrite');
      const store = tx.objectStore('sync_queue');
      const item = {
        operation_id: op.operation_id || `op_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
        entity_type: op.entity_type,
        entity_id: String(op.entity_id || ''),
        operation: op.operation || 'CREATE',
        payload: op.payload || {},
        status: 'PENDING',
        created_at: new Date().toISOString(),
      };
      const req = store.put(item);
      req.onsuccess = () => resolve(item);
      req.onerror = () => reject(req.error);
    });
  },

  getPendingQueue: async () => {
    const db = await openOfflineDB();
    return new Promise((resolve, reject) => {
      const tx = db.transaction('sync_queue', 'readonly');
      const store = tx.objectStore('sync_queue');
      const req = store.getAll();
      req.onsuccess = () => resolve(req.result || []);
      req.onerror = () => reject(req.error);
    });
  },

  removeQueueItem: async (operationId) => {
    const db = await openOfflineDB();
    return new Promise((resolve, reject) => {
      const tx = db.transaction('sync_queue', 'readwrite');
      const store = tx.objectStore('sync_queue');
      const req = store.delete(operationId);
      req.onsuccess = () => resolve(true);
      req.onerror = () => reject(req.error);
    });
  },

  clearQueue: async () => {
    const db = await openOfflineDB();
    return new Promise((resolve, reject) => {
      const tx = db.transaction('sync_queue', 'readwrite');
      const store = tx.objectStore('sync_queue');
      const req = store.clear();
      req.onsuccess = () => resolve(true);
      req.onerror = () => reject(req.error);
    });
  },

  // Cache Master Data
  cacheMasterData: async (data) => {
    const db = await openOfflineDB();
    const stores = ['employees', 'departments', 'holidays', 'attendance', 'leaves'];

    for (const storeName of stores) {
      if (data[storeName] && Array.isArray(data[storeName])) {
        const tx = db.transaction(storeName, 'readwrite');
        const store = tx.objectStore(storeName);
        store.clear();
        for (const item of data[storeName]) {
          store.put(item);
        }
      }
    }
  },

  // Fetch cached collection
  getCachedCollection: async (storeName) => {
    const db = await openOfflineDB();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(storeName, 'readonly');
      const store = tx.objectStore(storeName);
      const req = store.getAll();
      req.onsuccess = () => resolve(req.result || []);
      req.onerror = () => reject(req.error);
    });
  },
};
