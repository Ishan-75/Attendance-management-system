import React, { useState, useEffect } from 'react';
import { attendanceApi } from '../api/attendanceApi';
import { departmentApi } from '../api/departmentApi';
import { useToast } from '../context/ToastContext';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Input } from '../components/common/Input';
import { Select } from '../components/common/Select';
import { Badge } from '../components/common/Badge';
import { Modal } from '../components/common/Modal';
import { SkeletonLoader } from '../components/common/SkeletonLoader';
import { EmptyState } from '../components/common/EmptyState';
import {
  Calendar,
  Building2,
  Search,
  CheckCircle2,
  Save,
  RotateCcw,
  Edit3,
  Clock,
  AlertCircle
} from 'lucide-react';

const STATUS_OPTIONS = [
  { value: 'PRESENT', label: 'Present' },
  { value: 'ABSENT', label: 'Absent' },
  { value: 'LEAVE', label: 'Leave' },
  { value: 'WEEK_OFF', label: 'Week Off' },
  { value: 'HALF_DAY', label: 'Half Day' },
  { value: 'HOLIDAY', label: 'Holiday' },
  { value: 'WORK_FROM_HOME', label: 'Work From Home' },
];

export const Attendance = () => {
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [selectedDept, setSelectedDept] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [departments, setDepartments] = useState([]);
  const [sheetItems, setSheetItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  // Correction Modal State
  const [correctionTarget, setCorrectionTarget] = useState(null);
  const [correctionStatus, setCorrectionStatus] = useState('PRESENT');
  const [correctionCheckIn, setCorrectionCheckIn] = useState('09:00');
  const [correctionCheckOut, setCorrectionCheckOut] = useState('18:00');
  const [correctionReason, setCorrectionReason] = useState('');
  const [correctionRemarks, setCorrectionRemarks] = useState('');
  const [correctionLoading, setCorrectionLoading] = useState(false);

  const toast = useToast();

  // Load departments
  useEffect(() => {
    const fetchDepts = async () => {
      try {
        const res = await departmentApi.getDepartments(true);
        if (res.success) setDepartments(res.data);
      } catch (err) {
        // ignore
      }
    };
    fetchDepts();
  }, []);

  // Fetch sheet items for selected date and department
  const fetchSheet = async () => {
    setLoading(true);
    try {
      const res = await attendanceApi.getSheet(selectedDate, selectedDept || null, searchTerm);
      if (res.success) {
        // Format time objects to string HH:MM if necessary
        const formatted = res.data.map((item) => ({
          ...item,
          check_in_time: item.check_in_time ? String(item.check_in_time).slice(0, 5) : (item.status === 'PRESENT' ? '09:00' : ''),
          check_out_time: item.check_out_time ? String(item.check_out_time).slice(0, 5) : (item.status === 'PRESENT' ? '18:00' : ''),
        }));
        setSheetItems(formatted);
      }
    } catch (err) {
      toast.error('Failed to load attendance sheet');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSheet();
  }, [selectedDate, selectedDept]);

  // Search filter
  const handleSearchSubmit = (e) => {
    e.preventDefault();
    fetchSheet();
  };

  // Bulk set all statuses
  const handleSetAllStatus = (newStatus) => {
    setSheetItems((prev) =>
      prev.map((item) => ({
        ...item,
        status: newStatus,
        check_in_time: newStatus === 'PRESENT' || newStatus === 'WORK_FROM_HOME' ? '09:00' : (newStatus === 'HALF_DAY' ? '09:00' : ''),
        check_out_time: newStatus === 'PRESENT' || newStatus === 'WORK_FROM_HOME' ? '18:00' : (newStatus === 'HALF_DAY' ? '13:00' : ''),
      }))
    );
    toast.info(`Set all listed employees to ${newStatus}`);
  };

  // Modify individual row
  const handleRowChange = (index, field, value) => {
    setSheetItems((prev) => {
      const updated = [...prev];
      updated[index] = { ...updated[index], [field]: value };
      
      // Auto fill default times if changed to PRESENT
      if (field === 'status') {
        if (value === 'PRESENT' || value === 'WORK_FROM_HOME') {
          if (!updated[index].check_in_time) updated[index].check_in_time = '09:00';
          if (!updated[index].check_out_time) updated[index].check_out_time = '18:00';
        } else if (value === 'HALF_DAY') {
          if (!updated[index].check_in_time) updated[index].check_in_time = '09:00';
          if (!updated[index].check_out_time) updated[index].check_out_time = '13:00';
        } else if (value === 'ABSENT' || value === 'LEAVE' || value === 'WEEK_OFF' || value === 'HOLIDAY') {
          updated[index].check_in_time = '';
          updated[index].check_out_time = '';
        }
      }
      return updated;
    });
  };

  // Save all bulk records
  const handleSaveAll = async () => {
    setSaving(true);
    try {
      const records = sheetItems.map((item) => ({
        employee_id: item.employee_id,
        status: item.status,
        check_in_time: item.check_in_time ? `${item.check_in_time}:00` : null,
        check_out_time: item.check_out_time ? `${item.check_out_time}:00` : null,
        remarks: item.remarks || null,
      }));

      await attendanceApi.markBulk(selectedDate, records);
      toast.success(`Attendance successfully saved for ${records.length} employees`);
      fetchSheet();
    } catch (err) {
      toast.error(err.response?.data?.message || 'Failed to save attendance records');
    } finally {
      setSaving(false);
    }
  };

  // Open correction modal for marked record
  const handleOpenCorrection = (item) => {
    setCorrectionTarget(item);
    setCorrectionStatus(item.status || 'PRESENT');
    setCorrectionCheckIn(item.check_in_time || '09:00');
    setCorrectionCheckOut(item.check_out_time || '18:00');
    setCorrectionReason('');
    setCorrectionRemarks(item.remarks || '');
  };

  // Submit attendance correction
  const handleSaveCorrection = async (e) => {
    e.preventDefault();
    if (!correctionReason.trim()) {
      toast.error('A mandatory correction reason is required');
      return;
    }
    if (!correctionTarget.attendance_id) {
      toast.error('This record has not been saved to database yet');
      return;
    }

    setCorrectionLoading(true);
    try {
      await attendanceApi.correctAttendance(correctionTarget.attendance_id, {
        status: correctionStatus,
        check_in_time: correctionCheckIn ? `${correctionCheckIn}:00` : null,
        check_out_time: correctionCheckOut ? `${correctionCheckOut}:00` : null,
        remarks: correctionRemarks || null,
        reason: correctionReason.trim(),
      });

      toast.success('Attendance correction saved and logged to audit trail');
      setCorrectionTarget(null);
      fetchSheet();
    } catch (err) {
      toast.error(err.response?.data?.message || 'Failed to apply attendance correction');
    } finally {
      setCorrectionLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Title & Actions */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white tracking-tight">
            Daily Attendance Sheet
          </h2>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Mark daily presence, adjust check-in/out hours, and perform audited corrections
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="md"
            onClick={fetchSheet}
            icon={RotateCcw}
          >
            Reset
          </Button>
          <Button
            variant="primary"
            size="md"
            loading={saving}
            onClick={handleSaveAll}
            icon={Save}
          >
            Save All Changes
          </Button>
        </div>
      </div>

      {/* Control Bar: Date Picker, Department Filter, Search & Bulk Actions */}
      <Card bodyClassName="p-4">
        <div className="flex flex-col lg:flex-row items-stretch lg:items-center justify-between gap-4">
          <div className="flex flex-wrap items-center gap-3">
            {/* Date Picker */}
            <div className="flex items-center gap-2 bg-slate-50 dark:bg-slate-800 px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-700">
              <Calendar className="w-4 h-4 text-blue-600 dark:text-blue-400" />
              <input
                type="date"
                value={selectedDate}
                onChange={(e) => setSelectedDate(e.target.value)}
                className="bg-transparent border-none text-xs font-semibold text-slate-800 dark:text-slate-200 focus:outline-none"
              />
            </div>

            {/* Department Filter */}
            <div className="w-48">
              <select
                value={selectedDept}
                onChange={(e) => setSelectedDept(e.target.value)}
                className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-xs font-medium rounded-xl px-3 py-2 text-slate-800 dark:text-slate-200 focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All Departments</option>
                {departments.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Search Input */}
            <form onSubmit={handleSearchSubmit} className="relative w-56">
              <input
                type="text"
                placeholder="Search employee..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-xs rounded-xl pl-8 pr-3 py-2 text-slate-800 dark:text-slate-200 focus:ring-2 focus:ring-blue-500"
              />
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-3" />
            </form>
          </div>

          {/* Quick Bulk Action Buttons */}
          <div className="flex items-center gap-2 border-t lg:border-t-0 pt-3 lg:pt-0 border-slate-100 dark:border-slate-800">
            <span className="text-xs font-semibold text-slate-400 mr-1">Quick:</span>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => handleSetAllStatus('PRESENT')}
            >
              All Present
            </Button>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => handleSetAllStatus('ABSENT')}
            >
              All Absent
            </Button>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => handleSetAllStatus('WEEK_OFF')}
            >
              All Off
            </Button>
          </div>
        </div>
      </Card>

      {/* Attendance Interactive Marking Sheet */}
      <Card bodyClassName="p-0">
        {loading ? (
          <SkeletonLoader rows={6} type="table" />
        ) : sheetItems.length === 0 ? (
          <EmptyState
            title="No active employees found"
            description="There are no active employees configured for this department or search query."
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-200 dark:border-slate-800 bg-slate-50/80 dark:bg-slate-900/60 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                  <th className="py-3.5 px-4 pl-6">Employee</th>
                  <th className="py-3.5 px-4">Department</th>
                  <th className="py-3.5 px-4">Status</th>
                  <th className="py-3.5 px-4">Check In</th>
                  <th className="py-3.5 px-4">Check Out</th>
                  <th className="py-3.5 px-4">Remarks</th>
                  <th className="py-3.5 px-4 pr-6 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800/80 text-sm text-slate-700 dark:text-slate-200">
                {sheetItems.map((item, idx) => (
                  <tr
                    key={item.employee_id}
                    className="hover:bg-slate-50/60 dark:hover:bg-slate-800/40 transition-colors"
                  >
                    {/* Employee Info */}
                    <td className="py-3.5 px-4 pl-6">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-950/80 text-blue-700 dark:text-blue-300 flex items-center justify-center font-bold text-xs shrink-0">
                          {item.full_name.charAt(0)}
                        </div>
                        <div>
                          <div className="font-semibold text-slate-900 dark:text-white">
                            {item.full_name}
                          </div>
                          <div className="text-xs text-slate-400 font-mono">
                            {item.employee_code}
                          </div>
                        </div>
                      </div>
                    </td>

                    {/* Department */}
                    <td className="py-3.5 px-4 text-xs text-slate-500 dark:text-slate-400">
                      {item.department_name}
                    </td>

                    {/* Status Selector */}
                    <td className="py-3.5 px-4">
                      <select
                        value={item.status}
                        onChange={(e) => handleRowChange(idx, 'status', e.target.value)}
                        className={`text-xs font-semibold rounded-lg px-2.5 py-1.5 border transition-all cursor-pointer ${
                          item.status === 'PRESENT'
                            ? 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/60 dark:text-emerald-300 dark:border-emerald-800'
                            : item.status === 'ABSENT'
                            ? 'bg-rose-50 text-rose-700 border-rose-200 dark:bg-rose-950/60 dark:text-rose-300 dark:border-rose-800'
                            : item.status === 'LEAVE'
                            ? 'bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/60 dark:text-amber-300 dark:border-amber-800'
                            : item.status === 'HALF_DAY'
                            ? 'bg-orange-50 text-orange-700 border-orange-200 dark:bg-orange-950/60 dark:text-orange-300 dark:border-orange-800'
                            : item.status === 'WORK_FROM_HOME'
                            ? 'bg-cyan-50 text-cyan-700 border-cyan-200 dark:bg-cyan-950/60 dark:text-cyan-300 dark:border-cyan-800'
                            : 'bg-slate-100 text-slate-700 border-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-700'
                        }`}
                      >
                        {STATUS_OPTIONS.map((opt) => (
                          <option key={opt.value} value={opt.value}>
                            {opt.label}
                          </option>
                        ))}
                      </select>
                    </td>

                    {/* Check In Time */}
                    <td className="py-3.5 px-4">
                      <input
                        type="time"
                        value={item.check_in_time || ''}
                        disabled={item.status === 'ABSENT' || item.status === 'LEAVE' || item.status === 'WEEK_OFF'}
                        onChange={(e) => handleRowChange(idx, 'check_in_time', e.target.value)}
                        className="text-xs bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-2 py-1 text-slate-800 dark:text-slate-200 disabled:opacity-40"
                      />
                    </td>

                    {/* Check Out Time */}
                    <td className="py-3.5 px-4">
                      <input
                        type="time"
                        value={item.check_out_time || ''}
                        disabled={item.status === 'ABSENT' || item.status === 'LEAVE' || item.status === 'WEEK_OFF'}
                        onChange={(e) => handleRowChange(idx, 'check_out_time', e.target.value)}
                        className="text-xs bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-2 py-1 text-slate-800 dark:text-slate-200 disabled:opacity-40"
                      />
                    </td>

                    {/* Remarks Input */}
                    <td className="py-3.5 px-4">
                      <input
                        type="text"
                        placeholder="Optional remarks"
                        value={item.remarks || ''}
                        onChange={(e) => handleRowChange(idx, 'remarks', e.target.value)}
                        className="text-xs bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-2.5 py-1 text-slate-800 dark:text-slate-200 w-full max-w-[180px]"
                      />
                    </td>

                    {/* Action Buttons */}
                    <td className="py-3.5 px-4 pr-6 text-right">
                      {item.attendance_id ? (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleOpenCorrection(item)}
                          className="text-xs text-blue-600 hover:text-blue-700 dark:text-blue-400"
                        >
                          <Edit3 className="w-3.5 h-3.5 mr-1" />
                          Correct
                        </Button>
                      ) : (
                        <span className="text-[11px] text-slate-400">Unsaved</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Attendance Correction Modal with Mandatory Reason */}
      <Modal
        isOpen={!!correctionTarget}
        onClose={() => setCorrectionTarget(null)}
        title="Correct Attendance Record"
        subtitle={`Editing record for ${correctionTarget?.full_name} (${correctionTarget?.employee_code}) on ${selectedDate}`}
      >
        <form onSubmit={handleSaveCorrection} className="space-y-4">
          <div className="p-3 bg-amber-50 border border-amber-200 text-amber-900 dark:bg-amber-950/60 dark:border-amber-800 dark:text-amber-200 rounded-xl text-xs flex items-start gap-2.5">
            <AlertCircle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
            <span>
              All attendance corrections are permanently recorded in the system audit trail along with your stated reason.
            </span>
          </div>

          <Select
            label="Corrected Status"
            value={correctionStatus}
            onChange={(e) => setCorrectionStatus(e.target.value)}
            options={STATUS_OPTIONS}
            required
          />

          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Check In Time"
              type="time"
              value={correctionCheckIn}
              onChange={(e) => setCorrectionCheckIn(e.target.value)}
            />
            <Input
              label="Check Out Time"
              type="time"
              value={correctionCheckOut}
              onChange={(e) => setCorrectionCheckOut(e.target.value)}
            />
          </div>

          <Input
            label="Correction Reason"
            required
            placeholder="e.g. Employee attended site visit but biometric punch was missed"
            value={correctionReason}
            onChange={(e) => setCorrectionReason(e.target.value)}
            helperText="Provide a clear, detailed justification."
          />

          <Input
            label="Updated Remarks"
            placeholder="Optional additional notes"
            value={correctionRemarks}
            onChange={(e) => setCorrectionRemarks(e.target.value)}
          />

          <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-100 dark:border-slate-800">
            <Button
              variant="outline"
              size="md"
              onClick={() => setCorrectionTarget(null)}
              disabled={correctionLoading}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              size="md"
              loading={correctionLoading}
            >
              Apply Correction & Log
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
