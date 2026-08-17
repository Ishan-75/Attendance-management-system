import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { employeeApi } from '../api/employeeApi';
import { attendanceApi } from '../api/attendanceApi';
import { leaveApi } from '../api/leaveApi';
import { useToast } from '../context/ToastContext';
import { useAuth } from '../context/AuthContext';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { SkeletonLoader } from '../components/common/SkeletonLoader';
import { ConfirmDialog } from '../components/common/ConfirmDialog';
import {
  ArrowLeft,
  Calendar,
  Phone,
  Building,
  Briefcase,
  Clock,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  ChevronLeft,
  ChevronRight,
  User,
  Trash2
} from 'lucide-react';

export const EmployeeDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { isAdmin } = useAuth();
  const [employee, setEmployee] = useState(null);
  const [calendarData, setCalendarData] = useState(null);
  const [leaves, setLeaves] = useState([]);
  const [loading, setLoading] = useState(true);

  // Delete State
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState(false);

  const currentDate = new Date();
  const [selectedYear, setSelectedYear] = useState(currentDate.getFullYear());
  const [selectedMonth, setSelectedMonth] = useState(currentDate.getMonth() + 1);

  const toast = useToast();

  const fetchEmployeeData = async () => {
    setLoading(true);
    try {
      const [empRes, calRes, leaveRes] = await Promise.all([
        employeeApi.getEmployee(id),
        attendanceApi.getEmployeeCalendar(id, selectedYear, selectedMonth),
        leaveApi.getLeaves({ employee_id: id, limit: 10 }),
      ]);

      if (empRes.success) setEmployee(empRes.data);
      if (calRes.success) setCalendarData(calRes.data);
      if (leaveRes.success && leaveRes.data) setLeaves(leaveRes.data.items);
    } catch (err) {
      toast.error('Failed to load employee details');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEmployeeData();
  }, [id, selectedYear, selectedMonth]);

  const handlePrevMonth = () => {
    if (selectedMonth === 1) {
      setSelectedMonth(12);
      setSelectedYear((y) => y - 1);
    } else {
      setSelectedMonth((m) => m - 1);
    }
  };

  const handleNextMonth = () => {
    if (selectedMonth === 12) {
      setSelectedMonth(1);
      setSelectedYear((y) => y + 1);
    } else {
      setSelectedMonth((m) => m + 1);
    }
  };

  const handleDeleteEmployee = async () => {
    if (!employee) return;
    setDeleteLoading(true);
    try {
      await employeeApi.deleteEmployee(employee.id);
      toast.success(`Employee ${employee.full_name || employee.first_name} deleted successfully`);
      navigate('/employees');
    } catch (err) {
      toast.error(err.response?.data?.message || 'Failed to delete employee');
    } finally {
      setDeleteLoading(false);
    }
  };

  if (loading && !employee) {
    return (
      <div className="space-y-6">
        <div className="h-8 bg-slate-200 dark:bg-slate-800 rounded-lg w-48 animate-pulse" />
        <SkeletonLoader rows={4} type="card" />
        <div className="h-96 bg-slate-200 dark:bg-slate-800 rounded-2xl animate-pulse" />
      </div>
    );
  }

  if (!employee) {
    return (
      <div className="text-center py-12">
        <h3 className="text-lg font-bold text-slate-800 dark:text-slate-200">Employee not found</h3>
        <Link to="/employees" className="mt-4 inline-block">
          <Button variant="primary">Back to Directory</Button>
        </Link>
      </div>
    );
  }

  const monthNames = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
  ];

  return (
    <div className="space-y-8">
      {/* Back Link & Admin Actions */}
      <div className="flex items-center justify-between">
        <Link
          to="/employees"
          className="inline-flex items-center gap-2 text-xs font-semibold text-slate-500 hover:text-slate-900 dark:hover:text-slate-200 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Employee Directory
        </Link>

        {isAdmin && (
          <Button
            variant="outline"
            size="sm"
            icon={Trash2}
            className="text-rose-600 border-rose-200 hover:bg-rose-50 dark:border-rose-900 dark:hover:bg-rose-950/40"
            onClick={() => setDeleteOpen(true)}
          >
            Delete Employee
          </Button>
        )}
      </div>

      {/* Profile Header Banner */}
      <Card bodyClassName="p-6">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
          <div className="flex items-center gap-5">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-blue-600 to-indigo-600 text-white flex items-center justify-center text-2xl font-bold shadow-lg shadow-blue-500/20 shrink-0">
              {employee.first_name ? employee.first_name.charAt(0).toUpperCase() : 'E'}
            </div>

            <div>
              <div className="flex flex-wrap items-center gap-3">
                <h2 className="text-2xl font-bold text-slate-900 dark:text-white tracking-tight">
                  {employee.full_name || employee.first_name}
                </h2>
                <Badge variant={employee.status} size="md" dot>
                  {employee.status}
                </Badge>
              </div>

              <div className="flex flex-wrap items-center gap-y-1 gap-x-4 text-xs text-slate-500 dark:text-slate-400 mt-1.5">
                <span className="font-mono font-semibold text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-950 px-2 py-0.5 rounded-md">
                  {employee.employee_id}
                </span>
                <span>•</span>
                <span className="flex items-center gap-1">
                  <Briefcase className="w-3.5 h-3.5" />
                  {employee.designation || 'Staff'}
                </span>
                <span>•</span>
                <span className="flex items-center gap-1">
                  <Building className="w-3.5 h-3.5" />
                  {employee.department?.name || 'Unassigned'}
                </span>
              </div>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3 text-xs text-slate-600 dark:text-slate-300">
            {employee.phone ? (
              <div className="flex items-center gap-1.5 bg-slate-50 dark:bg-slate-800/80 px-3.5 py-2 rounded-xl border border-slate-200/80 dark:border-slate-700/80">
                <Phone className="w-3.5 h-3.5 text-blue-500" />
                <span className="font-mono font-medium">{employee.phone}</span>
              </div>
            ) : (
              <span className="text-slate-400 text-xs italic">No contact number provided</span>
            )}
          </div>
        </div>

        {/* Details Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-6 mt-6 border-t border-slate-100 dark:border-slate-800 text-xs">
          <div>
            <span className="text-slate-400 block mb-1">Employment Type</span>
            <span className="font-semibold text-slate-800 dark:text-slate-200">
              {(employee.employment_type || 'FULL_TIME').replace('_', ' ')}
            </span>
          </div>
          <div>
            <span className="text-slate-400 block mb-1">Joining Date</span>
            <span className="font-semibold text-slate-800 dark:text-slate-200 font-mono">
              {employee.joining_date || 'Not specified'}
            </span>
          </div>
        </div>
      </Card>

      {/* Monthly Attendance Summary KPI Bar */}
      {calendarData && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-bold text-slate-900 dark:text-white">
              Attendance Analytics ({monthNames[selectedMonth - 1]} {selectedYear})
            </h3>

            {/* Month Switcher */}
            <div className="flex items-center gap-2 bg-white dark:bg-slate-900 p-1 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
              <button
                onClick={handlePrevMonth}
                className="p-1.5 rounded-lg text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <span className="text-xs font-bold px-2 text-slate-800 dark:text-slate-200">
                {monthNames[selectedMonth - 1]} {selectedYear}
              </span>
              <button
                onClick={handleNextMonth}
                className="p-1.5 rounded-lg text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            <div className="p-4 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800">
              <span className="text-[11px] font-semibold text-slate-400 uppercase">Attendance %</span>
              <div className="text-xl font-bold text-blue-600 dark:text-blue-400 mt-1">
                {calendarData.attendance_percentage}%
              </div>
            </div>

            <div className="p-4 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800">
              <span className="text-[11px] font-semibold text-slate-400 uppercase">Present Days</span>
              <div className="text-xl font-bold text-emerald-600 dark:text-emerald-400 mt-1">
                {calendarData.present_days}
              </div>
            </div>

            <div className="p-4 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800">
              <span className="text-[11px] font-semibold text-slate-400 uppercase">Absent Days</span>
              <div className="text-xl font-bold text-rose-600 dark:text-rose-400 mt-1">
                {calendarData.absent_days}
              </div>
            </div>

            <div className="p-4 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800">
              <span className="text-[11px] font-semibold text-slate-400 uppercase">Leave Days</span>
              <div className="text-xl font-bold text-amber-600 dark:text-amber-400 mt-1">
                {calendarData.leave_days}
              </div>
            </div>

            <div className="p-4 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800">
              <span className="text-[11px] font-semibold text-slate-400 uppercase">Total Hours</span>
              <div className="text-xl font-bold text-slate-800 dark:text-slate-200 mt-1">
                {calendarData.total_hours_worked}h
              </div>
            </div>

            <div className="p-4 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800">
              <span className="text-[11px] font-semibold text-slate-400 uppercase">Overtime</span>
              <div className="text-xl font-bold text-indigo-600 dark:text-indigo-400 mt-1">
                {calendarData.total_overtime_hours}h
              </div>
            </div>
          </div>

          {/* Monthly Attendance Calendar Grid */}
          <Card
            title="Monthly Attendance Grid"
            subtitle={`Day-by-day attendance status for ${monthNames[selectedMonth - 1]} ${selectedYear}`}
          >
            <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-7 gap-2 pt-2">
              {calendarData.calendar_days.map((day) => {
                const dayNum = new Date(day.date).getDate();
                const dayName = new Date(day.date).toLocaleDateString('en-US', { weekday: 'short' });

                return (
                  <div
                    key={day.date}
                    className={`p-3 rounded-xl border transition-all flex flex-col justify-between min-h-[90px] ${
                      day.status === 'PRESENT'
                        ? 'bg-emerald-50/70 border-emerald-200/80 dark:bg-emerald-950/40 dark:border-emerald-800/60'
                        : day.status === 'ABSENT'
                        ? 'bg-rose-50/70 border-rose-200/80 dark:bg-rose-950/40 dark:border-rose-800/60'
                        : day.status === 'LEAVE'
                        ? 'bg-amber-50/70 border-amber-200/80 dark:bg-amber-950/40 dark:border-amber-800/60'
                        : day.status === 'HALF_DAY'
                        ? 'bg-orange-50/70 border-orange-200/80 dark:bg-orange-950/40 dark:border-orange-800/60'
                        : day.status === 'HOLIDAY'
                        ? 'bg-purple-50/70 border-purple-200/80 dark:bg-purple-950/40 dark:border-purple-800/60'
                        : day.status === 'WORK_FROM_HOME'
                        ? 'bg-cyan-50/70 border-cyan-200/80 dark:bg-cyan-950/40 dark:border-cyan-800/60'
                        : day.status === 'WEEK_OFF'
                        ? 'bg-slate-50/80 border-slate-200/70 dark:bg-slate-800/40 dark:border-slate-700/50 opacity-75'
                        : 'bg-slate-50 border-dashed border-slate-200 dark:bg-slate-900/30 dark:border-slate-800 opacity-50'
                    }`}
                  >
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-bold text-slate-800 dark:text-slate-200">
                        {dayNum}
                      </span>
                      <span className="text-[10px] uppercase font-semibold text-slate-400">
                        {dayName}
                      </span>
                    </div>

                    <div className="my-1">
                      {day.status ? (
                        <Badge variant={day.status} size="sm">
                          {day.status === 'WORK_FROM_HOME' ? 'WFH' : (day.status === 'WEEK_OFF' ? 'OFF' : day.status)}
                        </Badge>
                      ) : (
                        <span className="text-[10px] text-slate-400">No data</span>
                      )}
                    </div>

                    <div className="text-[10px] text-slate-500 font-mono flex items-center justify-between">
                      {day.check_in_time && day.check_out_time ? (
                        <span>{String(day.check_in_time).slice(0, 5)} - {String(day.check_out_time).slice(0, 5)}</span>
                      ) : day.holiday_name ? (
                        <span className="truncate">{day.holiday_name}</span>
                      ) : day.remarks ? (
                        <span className="truncate">{day.remarks}</span>
                      ) : (
                        <span>-</span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </Card>
        </div>
      )}

      {/* Leave History Table */}
      <Card
        title="Leave History"
        subtitle="Recent leave applications submitted by this employee"
      >
        {leaves.length === 0 ? (
          <div className="py-8 text-center text-xs text-slate-400">
            No leave requests recorded for this employee.
          </div>
        ) : (
          <div className="divide-y divide-slate-100 dark:divide-slate-800">
            {leaves.map((leave) => (
              <div key={leave.id} className="py-3.5 flex items-center justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2">
                    <Badge variant={leave.leave_type} size="sm">
                      {leave.leave_type}
                    </Badge>
                    <span className="text-xs font-semibold text-slate-800 dark:text-slate-200">
                      {leave.start_date} to {leave.end_date} ({leave.number_of_days} days)
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                    Reason: "{leave.reason}"
                  </p>
                </div>
                <Badge variant={leave.status} size="md" dot>
                  {leave.status}
                </Badge>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Delete Employee Confirmation Dialog (Admin Only) */}
      <ConfirmDialog
        isOpen={deleteOpen}
        title="Delete Employee"
        message={`Are you sure you want to delete ${employee?.full_name || employee?.first_name} (${employee?.employee_id})? This action will remove the employee from directory while retaining attendance audit records.`}
        confirmLabel="Delete Employee"
        confirmVariant="danger"
        loading={deleteLoading}
        onCancel={() => setDeleteOpen(false)}
        onConfirm={handleDeleteEmployee}
      />
    </div>
  );
};
