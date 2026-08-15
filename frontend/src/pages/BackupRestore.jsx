import React, { useState, useEffect } from 'react';
import { backupApi } from '../api/backupApi';
import { useToast } from '../context/ToastContext';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Table } from '../components/common/Table';
import { SkeletonLoader } from '../components/common/SkeletonLoader';
import { EmptyState } from '../components/common/EmptyState';
import { ConfirmDialog } from '../components/common/ConfirmDialog';
import {
  Database,
  Plus,
  Download,
  RotateCcw,
  ShieldAlert,
  HardDrive,
  FileCheck,
  AlertTriangle
} from 'lucide-react';

export const BackupRestore = () => {
  const [backups, setBackups] = useState([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);

  // Restore dialog state
  const [restoreTarget, setRestoreTarget] = useState(null);
  const [restoring, setRestoring] = useState(false);

  const toast = useToast();

  const fetchBackups = async () => {
    setLoading(true);
    try {
      const res = await backupApi.getBackups();
      if (res.success) setBackups(res.data);
    } catch (err) {
      toast.error('Failed to retrieve backups');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBackups();
  }, []);

  const handleCreateBackup = async () => {
    setCreating(true);
    try {
      const res = await backupApi.createBackup();
      toast.success(`Database backup created: ${res.data.filename}`);
      fetchBackups();
    } catch (err) {
      toast.error(err.response?.data?.message || 'Backup creation failed');
    } finally {
      setCreating(false);
    }
  };

  const handleDownload = (backupId) => {
    const url = backupApi.getDownloadUrl(backupId);
    window.open(url, '_blank');
  };

  const handleConfirmRestore = async () => {
    if (!restoreTarget) return;
    setRestoring(true);
    try {
      await backupApi.restoreBackup(restoreTarget.id, true);
      toast.success(`Database successfully restored from ${restoreTarget.filename}`);
      setRestoreTarget(null);
      fetchBackups();
    } catch (err) {
      toast.error(err.response?.data?.message || 'Database restore failed');
    } finally {
      setRestoring(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Title & Actions */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white tracking-tight">
            Database Backup & Recovery
          </h2>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Create online point-in-time database snapshots and safely restore system records
          </p>
        </div>

        <Button
          variant="primary"
          size="md"
          loading={creating}
          onClick={handleCreateBackup}
          icon={Plus}
        >
          Create Live Backup
        </Button>
      </div>

      {/* Safety Notice Card */}
      <div className="p-4 rounded-2xl bg-blue-50/80 border border-blue-200/80 dark:bg-blue-950/40 dark:border-blue-800 text-xs text-blue-900 dark:text-blue-200 flex items-start gap-3">
        <ShieldAlert className="w-5 h-5 text-blue-600 dark:text-blue-400 shrink-0 mt-0.5" />
        <div className="space-y-1">
          <p className="font-semibold text-sm">Enterprise Backup Policy</p>
          <p className="text-slate-600 dark:text-slate-300">
            Backups use safe online streaming. When executing a restore, an automatic pre-restore safety snapshot is created immediately prior to applying changes, and an immutable entry is logged to the system audit trail.
          </p>
        </div>
      </div>

      {/* Backups List */}
      <Card bodyClassName="p-0">
        {loading ? (
          <SkeletonLoader rows={5} type="table" />
        ) : backups.length === 0 ? (
          <EmptyState
            icon={Database}
            title="No database backups found"
            description="Create your first database snapshot now to ensure business continuity."
            actionLabel="Create Live Backup"
            onAction={handleCreateBackup}
          />
        ) : (
          <Table headers={['Backup Filename', 'Engine', 'File Size', 'Created At', 'Created By', { label: 'Actions', align: 'right' }]}>
            {backups.map((b) => (
              <tr key={b.id} className="hover:bg-slate-50/60 dark:hover:bg-slate-800/40 transition-colors">
                <td className="py-3.5 px-4 pl-6 font-mono text-xs font-semibold text-slate-900 dark:text-white flex items-center gap-2">
                  <HardDrive className="w-4 h-4 text-slate-400" />
                  {b.filename}
                </td>

                <td className="py-3.5 px-4">
                  <span className="text-[11px] font-mono uppercase font-bold px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300">
                    {b.db_type}
                  </span>
                </td>

                <td className="py-3.5 px-4 text-xs font-mono font-medium text-slate-600 dark:text-slate-300">
                  {b.size_human}
                </td>

                <td className="py-3.5 px-4 text-xs text-slate-500 font-mono">
                  {new Date(b.created_at).toLocaleString()}
                </td>

                <td className="py-3.5 px-4 text-xs text-slate-600 dark:text-slate-400">
                  {b.creator_name || 'Admin'}
                </td>

                <td className="py-3.5 px-4 pr-6 text-right">
                  <div className="flex items-center justify-end gap-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      icon={Download}
                      onClick={() => handleDownload(b.id)}
                    >
                      Download
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      className="text-rose-600 hover:text-rose-700 hover:bg-rose-50 dark:hover:bg-rose-950 border-rose-200 dark:border-rose-800"
                      icon={RotateCcw}
                      onClick={() => setRestoreTarget(b)}
                    >
                      Restore
                    </Button>
                  </div>
                </td>
              </tr>
            ))}
          </Table>
        )}
      </Card>

      {/* Restore Confirmation Dialog */}
      <ConfirmDialog
        isOpen={!!restoreTarget}
        onClose={() => setRestoreTarget(null)}
        onConfirm={handleConfirmRestore}
        loading={restoring}
        title="Restore Database Snapshot"
        message={`WARNING: Restoring '${restoreTarget?.filename}' will replace the active database tables with this backup snapshot. A safety pre-restore backup will be created automatically. Are you sure you want to proceed?`}
        confirmText="Confirm Database Restore"
        variant="danger"
      />
    </div>
  );
};
