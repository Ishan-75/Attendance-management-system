import React, { useState, useEffect } from 'react';
import { auditApi } from '../api/auditApi';
import { useToast } from '../context/ToastContext';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { Modal } from '../components/common/Modal';
import { Table } from '../components/common/Table';
import { Pagination } from '../components/common/Pagination';
import { SkeletonLoader } from '../components/common/SkeletonLoader';
import { EmptyState } from '../components/common/EmptyState';
import {
  History,
  ShieldAlert,
  Search,
  Filter,
  Eye,
  Calendar,
  User,
  Activity
} from 'lucide-react';

const ACTIONS = [
  'LOGIN', 'LOGOUT', 'FAILED_LOGIN', 'ACCOUNT_LOCKED',
  'EMPLOYEE_CREATED', 'EMPLOYEE_UPDATED', 'EMPLOYEE_DEACTIVATED',
  'ATTENDANCE_CREATED', 'ATTENDANCE_UPDATED', 'ATTENDANCE_CORRECTED',
  'LEAVE_APPLIED', 'LEAVE_APPROVED', 'LEAVE_REJECTED',
  'DEPARTMENT_CREATED', 'DEPARTMENT_UPDATED',
  'HOLIDAY_CREATED', 'HOLIDAY_UPDATED',
  'SETTINGS_CHANGED', 'BACKUP_CREATED', 'BACKUP_RESTORED'
];

export const AuditLogs = () => {
  const [logs, setLogs] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);

  // Filters
  const [selectedAction, setSelectedAction] = useState('');
  const [selectedEntity, setSelectedEntity] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

  // Diff / Detail modal
  const [detailLog, setDetailLog] = useState(null);

  const toast = useToast();

  const fetchAuditLogs = async () => {
    setLoading(true);
    try {
      const res = await auditApi.getAuditLogs({
        page,
        page_size: 25,
        action: selectedAction || undefined,
        entity_type: selectedEntity || undefined,
        start_date: startDate || undefined,
        end_date: endDate || undefined,
      });
      if (res.success && res.data) {
        setLogs(res.data.items);
        setTotal(res.data.total);
        setTotalPages(res.data.total_pages);
      }
    } catch (err) {
      toast.error('Failed to load system audit logs');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAuditLogs();
  }, [page, selectedAction, selectedEntity, startDate, endDate]);

  const formatJson = (str) => {
    if (!str) return 'None';
    try {
      const parsed = JSON.parse(str);
      return JSON.stringify(parsed, null, 2);
    } catch (e) {
      return str;
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-slate-900 dark:text-white tracking-tight">
          System Audit Trail
        </h2>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
          Immutable, append-only security logs of all system operations, auth events, and attendance changes
        </p>
      </div>

      {/* Filter Controls */}
      <Card bodyClassName="p-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1.5">
              Action Type
            </label>
            <select
              value={selectedAction}
              onChange={(e) => {
                setSelectedAction(e.target.value);
                setPage(1);
              }}
              className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-xs font-medium rounded-xl px-3 py-2 text-slate-800 dark:text-slate-200 focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Actions</option>
              {ACTIONS.map((a) => (
                <option key={a} value={a}>
                  {a}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1.5">
              Entity Type
            </label>
            <select
              value={selectedEntity}
              onChange={(e) => {
                setSelectedEntity(e.target.value);
                setPage(1);
              }}
              className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-xs font-medium rounded-xl px-3 py-2 text-slate-800 dark:text-slate-200 focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Entities</option>
              <option value="Attendance">Attendance</option>
              <option value="Employee">Employee</option>
              <option value="Leave">Leave</option>
              <option value="User">User</option>
              <option value="Department">Department</option>
              <option value="Holiday">Holiday</option>
              <option value="Backup">Backup</option>
              <option value="Setting">Setting</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1.5">
              From Date
            </label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => {
                setStartDate(e.target.value);
                setPage(1);
              }}
              className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-xs font-medium rounded-xl px-3 py-2 text-slate-800 dark:text-slate-200 focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1.5">
              To Date
            </label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => {
                setEndDate(e.target.value);
                setPage(1);
              }}
              className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-xs font-medium rounded-xl px-3 py-2 text-slate-800 dark:text-slate-200 focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
      </Card>

      {/* Audit Table */}
      <Card bodyClassName="p-0">
        {loading ? (
          <SkeletonLoader rows={8} type="table" />
        ) : logs.length === 0 ? (
          <EmptyState
            icon={History}
            title="No audit logs recorded"
            description="No events match your selected filtering options."
          />
        ) : (
          <div>
            <Table
              headers={[
                'Timestamp',
                'Actor / User',
                'Action',
                'Entity',
                'Description',
                'Client IP',
                { label: 'Details', align: 'right' },
              ]}
            >
              {logs.map((log) => (
                <tr key={log.id} className="hover:bg-slate-50/60 dark:hover:bg-slate-800/40 transition-colors">
                  <td className="py-3.5 px-4 pl-6 text-xs font-mono text-slate-500 dark:text-slate-400 whitespace-nowrap">
                    {new Date(log.timestamp).toLocaleString()}
                  </td>

                  <td className="py-3.5 px-4">
                    <span className="text-xs font-semibold text-slate-800 dark:text-slate-200">
                      {log.user_name || 'System'}
                    </span>
                  </td>

                  <td className="py-3.5 px-4">
                    <span className="inline-block text-[11px] font-mono font-semibold px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300">
                      {log.action}
                    </span>
                  </td>

                  <td className="py-3.5 px-4 text-xs text-slate-500">
                    {log.entity_type ? `${log.entity_type} ${log.entity_id ? '#' + log.entity_id : ''}` : '-'}
                  </td>

                  <td className="py-3.5 px-4 text-xs text-slate-700 dark:text-slate-300 max-w-sm truncate">
                    {log.description}
                  </td>

                  <td className="py-3.5 px-4 text-xs font-mono text-slate-400">
                    {log.ip_address || '-'}
                  </td>

                  <td className="py-3.5 px-4 pr-6 text-right">
                    {(log.old_value || log.new_value) && (
                      <Button
                        variant="ghost"
                        size="sm"
                        icon={Eye}
                        onClick={() => setDetailLog(log)}
                      >
                        Diff
                      </Button>
                    )}
                  </td>
                </tr>
              ))}
            </Table>

            <Pagination
              currentPage={page}
              totalPages={totalPages}
              totalItems={total}
              pageSize={25}
              onPageChange={setPage}
            />
          </div>
        )}
      </Card>

      {/* Audit Log Diff / Detail Modal */}
      <Modal
        isOpen={!!detailLog}
        onClose={() => setDetailLog(null)}
        maxWidth="max-w-2xl"
        title="Audit Event Details"
        subtitle={`${detailLog?.action} on ${detailLog?.entity_type || 'System'} at ${detailLog ? new Date(detailLog.timestamp).toLocaleString() : ''}`}
      >
        <div className="space-y-4">
          <div className="p-3.5 bg-slate-50 dark:bg-slate-800 rounded-xl text-xs space-y-1.5">
            <div>
              <strong className="text-slate-700 dark:text-slate-300">Description:</strong> {detailLog?.description}
            </div>
            <div>
              <strong className="text-slate-700 dark:text-slate-300">Actor:</strong> {detailLog?.user_name} ({detailLog?.ip_address || 'N/A'})
            </div>
            {detailLog?.user_agent && (
              <div className="text-slate-400 truncate">
                <strong>User Agent:</strong> {detailLog.user_agent}
              </div>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
            {/* Old Value */}
            <div>
              <div className="font-sans font-semibold text-slate-500 mb-1.5">Previous State (Old):</div>
              <pre className="p-3 bg-rose-50/50 dark:bg-rose-950/30 border border-rose-200/60 dark:border-rose-800/40 rounded-xl overflow-x-auto text-[11px] text-rose-900 dark:text-rose-200 max-h-60">
                {formatJson(detailLog?.old_value)}
              </pre>
            </div>

            {/* New Value */}
            <div>
              <div className="font-sans font-semibold text-slate-500 mb-1.5">New State (Modified):</div>
              <pre className="p-3 bg-emerald-50/50 dark:bg-emerald-950/30 border border-emerald-200/60 dark:border-emerald-800/40 rounded-xl overflow-x-auto text-[11px] text-emerald-900 dark:text-emerald-200 max-h-60">
                {formatJson(detailLog?.new_value)}
              </pre>
            </div>
          </div>

          <div className="flex justify-end pt-4 border-t border-slate-100 dark:border-slate-800">
            <Button variant="outline" size="md" onClick={() => setDetailLog(null)}>
              Close
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};
