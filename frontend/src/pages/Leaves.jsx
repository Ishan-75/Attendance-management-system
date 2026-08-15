import React, { useState, useEffect } from 'react';
import { leaveApi } from '../api/leaveApi';
import { employeeApi } from '../api/employeeApi';
import { useToast } from '../context/ToastContext';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Input } from '../components/common/Input';
import { Select } from '../components/common/Select';
import { Badge } from '../components/common/Badge';
import { Modal } from '../components/common/Modal';
import { Table } from '../components/common/Table';
import { Pagination } from '../components/common/Pagination';
import { SkeletonLoader } from '../components/common/SkeletonLoader';
import { EmptyState } from '../components/common/EmptyState';
import { ConfirmDialog } from '../components/common/ConfirmDialog';
import {
  CalendarDays,
  Plus,
  CheckCircle2,
  XCircle,
  Clock,
  User,
  AlertCircle
} from 'lucide-react';

const LEAVE_TYPES = [
  { value: 'CASUAL', label: 'Casual Leave' },
  { value: 'SICK', label: 'Sick Leave' },
  { value: 'EMERGENCY', label: 'Emergency Leave' },
  { value: 'ANNUAL', label: 'Annual Paid Leave' },
  { value: 'OTHER', label: 'Other' },
];

export const Leaves = () => {
  const [leaves, setLeaves] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState(''); // '' for all, or PENDING, APPROVED, REJECTED

  // Employees list for applying leave
  const [employees, setEmployees] = useState([]);

  // Apply Leave Modal
  const [applyModalOpen, setApplyModalOpen] = useState(false);
  const [formData, setFormData] = useState({
    employee_id: '',
    leave_type: 'CASUAL',
    start_date: new Date().toISOString().split('T')[0],
    end_date: new Date().toISOString().split('T')[0],
    number_of_days: 1.0,
    reason: '',
  });
  const [applyLoading, setApplyLoading] = useState(false);

  // Decision Modal (Approve / Reject)
  const [decisionTarget, setDecisionTarget] = useState(null);
  const [decisionType, setDecisionType] = useState(null); // 'approve' | 'reject'
  const [decisionReason, setDecisionReason] = useState('');
  const [decisionLoading, setDecisionLoading] = useState(false);

  const toast = useToast();

  useEffect(() => {
    const fetchEmployeesList = async () => {
      try {
        const res = await employeeApi.getEmployees({ limit: 100, status_filter: 'ACTIVE' });
        if (res.success && res.data) {
          setEmployees(res.data.items);
          if (res.data.items.length > 0 && !formData.employee_id) {
            setFormData((prev) => ({ ...prev, employee_id: res.data.items[0].id }));
          }
        }
      } catch (err) {}
    };
    fetchEmployeesList();
  }, []);

  const fetchLeaves = async () => {
    setLoading(true);
    try {
      const res = await leaveApi.getLeaves({
        page,
        page_size: 15,
        status_filter: statusFilter || undefined,
      });
      if (res.success && res.data) {
        setLeaves(res.data.items);
        setTotal(res.data.total);
        setTotalPages(res.data.total_pages);
      }
    } catch (err) {
      toast.error('Failed to load leave applications');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLeaves();
  }, [page, statusFilter]);

  // Auto calculate number of days when dates change
  const handleDateChange = (field, value) => {
    const updated = { ...formData, [field]: value };
    if (updated.start_date && updated.end_date) {
      const d1 = new Date(updated.start_date);
      const d2 = new Date(updated.end_date);
      if (d2 >= d1) {
        const diffTime = Math.abs(d2 - d1);
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1;
        updated.number_of_days = diffDays;
      }
    }
    setFormData(updated);
  };

  const handleApplySubmit = async (e) => {
    e.preventDefault();
    if (!formData.reason.trim()) {
      toast.error('Please enter a reason for the leave');
      return;
    }

    setApplyLoading(true);
    try {
      await leaveApi.applyLeave({
        ...formData,
        employee_id: Number(formData.employee_id),
        number_of_days: Number(formData.number_of_days),
      });
      toast.success('Leave application submitted successfully');
      setApplyModalOpen(false);
      fetchLeaves();
    } catch (err) {
      toast.error(err.response?.data?.message || 'Failed to submit leave');
    } finally {
      setApplyLoading(false);
    }
  };

  const handleDecisionSubmit = async () => {
    if (!decisionTarget || !decisionType) return;
    setDecisionLoading(true);
    try {
      if (decisionType === 'approve') {
        await leaveApi.approveLeave(decisionTarget.id, decisionReason);
        toast.success(`Leave approved for ${decisionTarget.employee?.full_name}`);
      } else {
        await leaveApi.rejectLeave(decisionTarget.id, decisionReason || 'Declined by manager');
        toast.info(`Leave request rejected for ${decisionTarget.employee?.full_name}`);
      }
      setDecisionTarget(null);
      setDecisionType(null);
      setDecisionReason('');
      fetchLeaves();
    } catch (err) {
      toast.error(err.response?.data?.message || 'Action failed');
    } finally {
      setDecisionLoading(false);
    }
  };

  const tabs = [
    { label: 'All Requests', value: '' },
    { label: 'Pending', value: 'PENDING' },
    { label: 'Approved', value: 'APPROVED' },
    { label: 'Rejected', value: 'REJECTED' },
  ];

  return (
    <div className="space-y-6">
      {/* Title & Actions */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white tracking-tight">
            Leave Management
          </h2>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Review, approve, and track employee leave requests with automated attendance syncing
          </p>
        </div>

        <Button
          variant="primary"
          size="md"
          onClick={() => setApplyModalOpen(true)}
          icon={Plus}
        >
          Apply Leave
        </Button>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-200 dark:border-slate-800">
        {tabs.map((tab) => (
          <button
            key={tab.value}
            onClick={() => {
              setStatusFilter(tab.value);
              setPage(1);
            }}
            className={`px-4 py-2.5 text-xs font-semibold border-b-2 transition-all cursor-pointer ${
              statusFilter === tab.value
                ? 'border-blue-600 text-blue-600 dark:border-blue-400 dark:text-blue-400'
                : 'border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Leave Requests Table */}
      <Card bodyClassName="p-0">
        {loading ? (
          <SkeletonLoader rows={6} type="table" />
        ) : leaves.length === 0 ? (
          <EmptyState
            icon={CalendarDays}
            title="No leave requests found"
            description="There are no leave requests matching the chosen status filter."
            actionLabel="Apply Leave"
            onAction={() => setApplyModalOpen(true)}
          />
        ) : (
          <div>
            <Table
              headers={[
                'Employee',
                'Leave Type',
                'Date Range',
                'Days',
                'Reason',
                'Status',
                { label: 'Actions', align: 'right' },
              ]}
            >
              {leaves.map((leave) => (
                <tr
                  key={leave.id}
                  className="hover:bg-slate-50/60 dark:hover:bg-slate-800/40 transition-colors"
                >
                  <td className="py-3.5 px-4 pl-6">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-950 text-blue-700 dark:text-blue-300 flex items-center justify-center font-bold text-xs shrink-0">
                        {leave.employee?.full_name?.charAt(0) || 'E'}
                      </div>
                      <div>
                        <div className="font-semibold text-slate-900 dark:text-white">
                          {leave.employee?.full_name}
                        </div>
                        <div className="text-xs text-slate-400 font-mono">
                          {leave.employee?.employee_id}
                        </div>
                      </div>
                    </div>
                  </td>

                  <td className="py-3.5 px-4">
                    <Badge variant={leave.leave_type} size="sm">
                      {leave.leave_type}
                    </Badge>
                  </td>

                  <td className="py-3.5 px-4 text-xs font-mono text-slate-600 dark:text-slate-300">
                    {leave.start_date} to {leave.end_date}
                  </td>

                  <td className="py-3.5 px-4 text-xs font-bold text-slate-800 dark:text-slate-200">
                    {leave.number_of_days} {leave.number_of_days === 1 ? 'day' : 'days'}
                  </td>

                  <td className="py-3.5 px-4 text-xs text-slate-600 dark:text-slate-400 max-w-xs truncate">
                    {leave.reason}
                  </td>

                  <td className="py-3.5 px-4">
                    <Badge variant={leave.status} size="sm" dot>
                      {leave.status}
                    </Badge>
                  </td>

                  <td className="py-3.5 px-4 pr-6 text-right">
                    {leave.status === 'PENDING' ? (
                      <div className="flex items-center justify-end gap-1.5">
                        <Button
                          variant="success"
                          size="sm"
                          onClick={() => {
                            setDecisionTarget(leave);
                            setDecisionType('approve');
                            setDecisionReason('');
                          }}
                        >
                          Approve
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            setDecisionTarget(leave);
                            setDecisionType('reject');
                            setDecisionReason('');
                          }}
                        >
                          Reject
                        </Button>
                      </div>
                    ) : (
                      <span className="text-xs text-slate-400">
                        {leave.status === 'APPROVED' ? `Approved by ${leave.approver_name || 'Manager'}` : (leave.rejection_reason || 'Rejected')}
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </Table>

            <Pagination
              currentPage={page}
              totalPages={totalPages}
              totalItems={total}
              pageSize={15}
              onPageChange={setPage}
            />
          </div>
        )}
      </Card>

      {/* Apply Leave Modal */}
      <Modal
        isOpen={applyModalOpen}
        onClose={() => setApplyModalOpen(false)}
        maxWidth="max-w-lg"
        title="Submit Leave Request"
        subtitle="Apply for leave on behalf of an employee"
      >
        <form onSubmit={handleApplySubmit} className="space-y-4">
          <Select
            label="Employee"
            required
            value={formData.employee_id}
            onChange={(e) => setFormData({ ...formData, employee_id: e.target.value })}
            options={employees.map((e) => ({
              value: e.id,
              label: `${e.full_name} (${e.employee_id}) - ${e.department?.name || 'Dept'}`,
            }))}
          />

          <Select
            label="Leave Type"
            required
            value={formData.leave_type}
            onChange={(e) => setFormData({ ...formData, leave_type: e.target.value })}
            options={LEAVE_TYPES}
          />

          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Start Date"
              type="date"
              required
              value={formData.start_date}
              onChange={(e) => handleDateChange('start_date', e.target.value)}
            />
            <Input
              label="End Date"
              type="date"
              required
              value={formData.end_date}
              onChange={(e) => handleDateChange('end_date', e.target.value)}
            />
          </div>

          <Input
            label="Total Days"
            type="number"
            step="0.5"
            min="0.5"
            required
            value={formData.number_of_days}
            onChange={(e) => setFormData({ ...formData, number_of_days: e.target.value })}
          />

          <Input
            label="Reason for Leave"
            required
            placeholder="e.g. Annual family vacation / Medical treatment"
            value={formData.reason}
            onChange={(e) => setFormData({ ...formData, reason: e.target.value })}
          />

          <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-100 dark:border-slate-800">
            <Button
              variant="outline"
              size="md"
              onClick={() => setApplyModalOpen(false)}
              disabled={applyLoading}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              size="md"
              loading={applyLoading}
            >
              Submit Application
            </Button>
          </div>
        </form>
      </Modal>

      {/* Decision Modal (Approve/Reject) */}
      <Modal
        isOpen={!!decisionTarget}
        onClose={() => setDecisionTarget(null)}
        title={decisionType === 'approve' ? 'Approve Leave Request' : 'Reject Leave Request'}
        subtitle={`Request #${decisionTarget?.id} by ${decisionTarget?.employee?.full_name} (${decisionTarget?.start_date} to ${decisionTarget?.end_date})`}
      >
        <div className="space-y-4">
          <p className="text-sm text-slate-600 dark:text-slate-300">
            {decisionType === 'approve'
              ? 'Approving this request will automatically synchronize attendance records for the entire duration and mark status as LEAVE with 0 hours.'
              : 'Please specify the justification or remarks for declining this leave request.'}
          </p>

          <Input
            label={decisionType === 'approve' ? 'Optional Notes' : 'Rejection Reason'}
            required={decisionType === 'reject'}
            placeholder={decisionType === 'approve' ? 'e.g. Approved by department head' : 'e.g. Insufficient coverage during release week'}
            value={decisionReason}
            onChange={(e) => setDecisionReason(e.target.value)}
          />

          <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-100 dark:border-slate-800">
            <Button
              variant="outline"
              size="md"
              onClick={() => setDecisionTarget(null)}
              disabled={decisionLoading}
            >
              Cancel
            </Button>
            <Button
              variant={decisionType === 'approve' ? 'primary' : 'danger'}
              size="md"
              loading={decisionLoading}
              onClick={handleDecisionSubmit}
            >
              {decisionType === 'approve' ? 'Confirm Approval' : 'Confirm Rejection'}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};
