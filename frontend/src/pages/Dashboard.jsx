import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { dashboardApi } from '../api/dashboardApi';
import { leaveApi } from '../api/leaveApi';
import { useToast } from '../context/ToastContext';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { SkeletonLoader } from '../components/common/SkeletonLoader';
import { ConfirmDialog } from '../components/common/ConfirmDialog';
import {
  Users,
  UserCheck,
  UserX,
  CalendarDays,
  Percent,
  ArrowUpRight,
  TrendingUp,
  Clock,
  Building2,
  Calendar,
  CheckCircle2,
  XCircle,
  Activity
} from 'lucide-react';

export const Dashboard = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [actionLeave, setActionLeave] = useState(null);
  const [actionType, setActionType] = useState(null); // 'approve' | 'reject'
  const [actionLoading, setActionLoading] = useState(false);

  const toast = useToast();

  const fetchDashboard = async (targetDate) => {
    setLoading(true);
    try {
      const res = await dashboardApi.getData(targetDate);
      if (res.success) {
        setData(res.data);
      }
    } catch (err) {
      toast.error('Failed to load dashboard metrics');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboard(selectedDate);
  }, [selectedDate]);

  const handleLeaveDecision = async () => {
    if (!actionLeave || !actionType) return;
    setActionLoading(true);
    try {
      if (actionType === 'approve') {
        await leaveApi.approveLeave(actionLeave.id);
        toast.success(`Leave approved for ${actionLeave.employee.full_name}`);
      } else {
        await leaveApi.rejectLeave(actionLeave.id, 'Declined from quick action dashboard');
        toast.info(`Leave rejected for ${actionLeave.employee.full_name}`);
      }
      fetchDashboard(selectedDate);
    } catch (err) {
      toast.error('Failed to process leave decision');
    } finally {
      setActionLoading(false);
      setActionLeave(null);
      setActionType(null);
    }
  };

  if (loading && !data) {
    return (
      <div className="space-y-6">
        <div className="h-8 bg-slate-200 dark:bg-slate-800 rounded-lg w-48 animate-pulse" />
        <SkeletonLoader rows={4} type="card" />
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 h-72 bg-slate-200 dark:bg-slate-800 rounded-2xl animate-pulse" />
          <div className="h-72 bg-slate-200 dark:bg-slate-800 rounded-2xl animate-pulse" />
        </div>
      </div>
    );
  }

  const { summary, trends, department_stats, pending_leaves, recent_activities } = data || {
    summary: {},
    trends: [],
    department_stats: [],
    pending_leaves: [],
    recent_activities: [],
  };

  const statCards = [
    {
      label: 'Active Employees',
      value: summary.active_employees || 0,
      sublabel: `Total: ${summary.total_employees || 0}`,
      icon: Users,
      color: 'blue',
    },
    {
      label: 'Present Today',
      value: summary.present_today || 0,
      sublabel: `${summary.wfh_today || 0} WFH / ${summary.half_day_today || 0} Half-day`,
      icon: UserCheck,
      color: 'emerald',
    },
    {
      label: 'Absent',
      value: summary.absent_today || 0,
      sublabel: `${summary.unmarked_today || 0} Unrecorded`,
      icon: UserX,
      color: 'rose',
    },
    {
      label: 'On Leave',
      value: summary.leave_today || 0,
      sublabel: `${summary.week_off_today || 0} Weekend Off`,
      icon: CalendarDays,
      color: 'amber',
    },
    {
      label: 'Attendance Rate',
      value: `${summary.attendance_rate || 0}%`,
      sublabel: 'Working pool efficiency',
      icon: Percent,
      color: 'indigo',
    },
  ];

  return (
    <div className="space-y-8">
      {/* Top Header with Date Selection */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white tracking-tight">
            Workforce Overview
          </h2>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Real-time daily attendance metrics and organizational health
          </p>
        </div>

        <div className="flex items-center gap-3 bg-white dark:bg-slate-900 p-1.5 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center gap-2 px-3 py-1 text-xs font-semibold text-slate-600 dark:text-slate-300">
            <Calendar className="w-4 h-4 text-blue-600 dark:text-blue-400" />
            <span>Date:</span>
          </div>
          <input
            type="date"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            className="bg-slate-50 dark:bg-slate-800 border-none text-xs font-medium rounded-xl px-3 py-1.5 text-slate-800 dark:text-slate-200 focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      {/* KPI Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        {statCards.map((card, idx) => {
          const Icon = card.icon;
          const colorStyles = {
            blue: 'bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-200/50',
            emerald: 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-200/50',
            rose: 'bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-200/50',
            amber: 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-200/50',
            indigo: 'bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 border-indigo-200/50',
          }[card.color];

          return (
            <div
              key={idx}
              className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/80 dark:border-slate-800 p-5 shadow-sm hover:shadow transition-shadow"
            >
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                  {card.label}
                </span>
                <div className={`w-9 h-9 rounded-xl flex items-center justify-center border ${colorStyles}`}>
                  <Icon className="w-4 h-4" />
                </div>
              </div>
              <div className="text-2xl font-bold text-slate-900 dark:text-white tracking-tight">
                {card.value}
              </div>
              <div className="text-xs font-medium text-slate-400 dark:text-slate-500 mt-1">
                {card.sublabel}
              </div>
            </div>
          );
        })}
      </div>

      {/* Charts & Department Breakdown Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 7-Day Trend Visualizer */}
        <Card
          title="7-Day Attendance Trend"
          subtitle="Daily presence rate (%) across active workforce"
          className="lg:col-span-2"
        >
          <div className="pt-2">
            <div className="grid grid-cols-7 gap-2 items-end h-48 border-b border-slate-100 dark:border-slate-800 pb-4">
              {trends.map((t, idx) => (
                <div key={idx} className="flex flex-col items-center gap-2 h-full justify-end group">
                  <span className="text-[11px] font-semibold text-slate-600 dark:text-slate-300 group-hover:text-blue-600 transition-colors">
                    {t.attendance_rate}%
                  </span>
                  <div className="w-full max-w-[36px] bg-slate-100 dark:bg-slate-800 rounded-t-xl overflow-hidden flex flex-col justify-end h-32 relative">
                    <div
                      style={{ height: `${Math.min(100, Math.max(5, t.attendance_rate))}%` }}
                      className="w-full bg-gradient-to-t from-blue-600 to-indigo-500 rounded-t-xl transition-all duration-500"
                    />
                  </div>
                  <span className="text-[11px] font-medium text-slate-400">
                    {t.formatted_date}
                  </span>
                </div>
              ))}
            </div>

            <div className="flex items-center justify-center gap-6 mt-4 text-xs text-slate-500">
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-blue-600" />
                <span>Attendance Rate %</span>
              </div>
            </div>
          </div>
        </Card>

        {/* Department Attendance Distribution */}
        <Card
          title="Department Presence"
          subtitle="Today's attendance rate by department"
        >
          <div className="space-y-4 pt-1">
            {department_stats.length === 0 ? (
              <p className="text-xs text-slate-400 py-6 text-center">No active departments</p>
            ) : (
              department_stats.map((dept) => (
                <div key={dept.department_id} className="space-y-1.5">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-slate-700 dark:text-slate-200">
                      {dept.department_name}
                    </span>
                    <span className="font-bold text-slate-900 dark:text-white">
                      {dept.attendance_rate}% ({dept.present}/{dept.total_employees})
                    </span>
                  </div>
                  <div className="h-2 w-full bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                    <div
                      style={{ width: `${dept.attendance_rate}%` }}
                      className="h-full bg-blue-600 rounded-full transition-all duration-500"
                    />
                  </div>
                </div>
              ))
            )}
          </div>
        </Card>
      </div>

      {/* Pending Leave Requests & Recent Activity Feed */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Pending Leaves Card */}
        <Card
          title="Pending Leave Applications"
          subtitle="Requests awaiting supervisor review"
          action={
            <Link
              to="/leaves"
              className="text-xs font-semibold text-blue-600 hover:text-blue-700 dark:text-blue-400 flex items-center gap-1"
            >
              View All <ArrowUpRight className="w-3.5 h-3.5" />
            </Link>
          }
        >
          <div className="divide-y divide-slate-100 dark:divide-slate-800">
            {pending_leaves.length === 0 ? (
              <div className="py-8 text-center text-xs text-slate-400">
                No pending leave requests at this time.
              </div>
            ) : (
              pending_leaves.map((leave) => (
                <div key={leave.id} className="py-3.5 first:pt-0 last:pb-0 flex items-center justify-between gap-4">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-bold text-slate-900 dark:text-white">
                        {leave.employee?.full_name}
                      </span>
                      <Badge variant={leave.leave_type} size="sm">
                        {leave.leave_type}
                      </Badge>
                    </div>
                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                      {leave.start_date} to {leave.end_date} ({leave.number_of_days} days) • Reason: "{leave.reason}"
                    </p>
                  </div>

                  <div className="flex items-center gap-1.5 shrink-0">
                    <Button
                      variant="success"
                      size="sm"
                      onClick={() => {
                        setActionLeave(leave);
                        setActionType('approve');
                      }}
                    >
                      Approve
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        setActionLeave(leave);
                        setActionType('reject');
                      }}
                    >
                      Reject
                    </Button>
                  </div>
                </div>
              ))
            )}
          </div>
        </Card>

        {/* Recent Audit Activities Feed */}
        <Card
          title="System Audit Feed"
          subtitle="Recent operational and workforce logs"
          action={
            <Link
              to="/audit-logs"
              className="text-xs font-semibold text-blue-600 hover:text-blue-700 dark:text-blue-400 flex items-center gap-1"
            >
              Audit Trail <ArrowUpRight className="w-3.5 h-3.5" />
            </Link>
          }
        >
          <div className="space-y-3.5">
            {recent_activities.length === 0 ? (
              <div className="py-8 text-center text-xs text-slate-400">
                No audit activity recorded yet.
              </div>
            ) : (
              recent_activities.map((log) => (
                <div key={log.id} className="flex items-start gap-3 text-xs">
                  <div className="w-6 h-6 rounded-full bg-blue-50 text-blue-600 dark:bg-blue-950 dark:text-blue-400 flex items-center justify-center shrink-0 mt-0.5">
                    <Activity className="w-3.5 h-3.5" />
                  </div>
                  <div className="flex-1">
                    <p className="text-slate-800 dark:text-slate-200 font-medium">
                      {log.description}
                    </p>
                    <div className="flex items-center gap-2 text-[10px] text-slate-400 mt-0.5">
                      <span>By {log.user_name}</span>
                      <span>•</span>
                      <span>{log.timestamp}</span>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </Card>
      </div>

      {/* Confirmation Dialog for Quick Leave Decision */}
      <ConfirmDialog
        isOpen={!!actionLeave}
        onClose={() => {
          setActionLeave(null);
          setActionType(null);
        }}
        onConfirm={handleLeaveDecision}
        loading={actionLoading}
        title={actionType === 'approve' ? 'Approve Leave Request' : 'Reject Leave Request'}
        message={
          actionType === 'approve'
            ? `Are you sure you want to approve leave for ${actionLeave?.employee?.full_name}? This will automatically mark their attendance records as LEAVE.`
            : `Are you sure you want to decline leave for ${actionLeave?.employee?.full_name}?`
        }
        confirmText={actionType === 'approve' ? 'Approve Leave' : 'Reject Leave'}
        variant={actionType === 'approve' ? 'primary' : 'danger'}
      />
    </div>
  );
};
