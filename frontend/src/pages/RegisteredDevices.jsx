import React, { useState, useEffect } from 'react';
import { syncApi } from '../api/syncApi';
import { useToast } from '../context/ToastContext';
import { Card } from '../components/common/Card';
import { Badge } from '../components/common/Badge';
import { Table } from '../components/common/Table';
import { SkeletonLoader } from '../components/common/SkeletonLoader';
import { EmptyState } from '../components/common/EmptyState';
import { Smartphone, RefreshCw, Laptop, ShieldCheck, Clock } from 'lucide-react';

export const RegisteredDevices = () => {
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(true);
  const toast = useToast();

  const fetchDevices = async () => {
    setLoading(true);
    try {
      const res = await syncApi.getDevices();
      if (res.success) {
        setDevices(res.data);
      }
    } catch (err) {
      toast.error('Failed to load registered devices');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDevices();
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white tracking-tight">
            Registered Devices & Synchronization Hub
          </h2>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Monitor client installations, last heartbeat synchronization timestamps, and device authorization status
          </p>
        </div>

        <button
          onClick={fetchDevices}
          className="flex items-center gap-2 px-4 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-xs font-semibold rounded-xl text-slate-700 dark:text-slate-200 hover:bg-slate-50 transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
          <span>Refresh</span>
        </button>
      </div>

      <Card bodyClassName="p-0">
        {loading ? (
          <SkeletonLoader rows={5} type="table" />
        ) : devices.length === 0 ? (
          <EmptyState
            icon={Smartphone}
            title="No devices registered yet"
            description="Client devices will automatically appear here upon performing their first synchronization."
          />
        ) : (
          <Table
            headers={[
              'Device Identity',
              'Device Name',
              'Platform',
              'App Version',
              'Last Synchronized',
              'Status'
            ]}
          >
            {devices.map((dev) => (
              <tr key={dev.id} className="hover:bg-slate-50/60 dark:hover:bg-slate-800/40 transition-colors">
                <td className="py-3.5 px-4 pl-6 font-mono text-xs font-bold text-blue-600 dark:text-blue-400">
                  {dev.device_id}
                </td>
                <td className="py-3.5 px-4 font-semibold text-slate-900 dark:text-white">
                  <div className="flex items-center gap-2">
                    {dev.platform === 'android' ? (
                      <Smartphone className="w-4 h-4 text-emerald-500" />
                    ) : (
                      <Laptop className="w-4 h-4 text-blue-500" />
                    )}
                    <span>{dev.device_name}</span>
                  </div>
                </td>
                <td className="py-3.5 px-4 text-xs uppercase font-mono text-slate-600 dark:text-slate-300">
                  {dev.platform}
                </td>
                <td className="py-3.5 px-4 font-mono text-xs text-slate-500">
                  v{dev.app_version || '1.0.0'}
                </td>
                <td className="py-3.5 px-4 font-mono text-xs text-slate-600 dark:text-slate-300">
                  {dev.last_sync_at ? new Date(dev.last_sync_at).toLocaleString() : 'Never'}
                </td>
                <td className="py-3.5 px-4 pr-6">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                    dev.is_active
                      ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800'
                      : 'bg-rose-50 text-rose-700 dark:bg-rose-950/60 dark:text-rose-300 border border-rose-200 dark:border-rose-800'
                  }`}>
                    {dev.is_active ? 'Active' : 'Revoked'}
                  </span>
                </td>
              </tr>
            ))}
          </Table>
        )}
      </Card>
    </div>
  );
};
