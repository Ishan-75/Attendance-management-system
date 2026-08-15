import React, { useState, useEffect } from 'react';
import { reportApi } from '../api/reportApi';
import { departmentApi } from '../api/departmentApi';
import { useToast } from '../context/ToastContext';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { Table } from '../components/common/Table';
import { SkeletonLoader } from '../components/common/SkeletonLoader';
import { EmptyState } from '../components/common/EmptyState';
import {
  FileSpreadsheet,
  Download,
  Filter,
  Calendar,
  Building,
  RefreshCw,
  FileText,
  FileCode,
  Printer,
  ChevronDown
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

export const Reports = () => {
  const todayStr = new Date().toISOString().split('T')[0];
  const firstDayStr = new Date(new Date().getFullYear(), new Date().getMonth(), 1).toISOString().split('T')[0];

  const [startDate, setStartDate] = useState(firstDayStr);
  const [endDate, setEndDate] = useState(todayStr);
  const [selectedDept, setSelectedDept] = useState('');
  const [selectedStatus, setSelectedStatus] = useState('');
  const [departments, setDepartments] = useState([]);

  const [reportRows, setReportRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(null); // 'excel' | 'csv' | 'json' | 'html'
  const [dropdownOpen, setDropdownOpen] = useState(false);

  const toast = useToast();

  useEffect(() => {
    const fetchDepts = async () => {
      try {
        const res = await departmentApi.getDepartments(true);
        if (res.success) setDepartments(res.data);
      } catch (err) {}
    };
    fetchDepts();
  }, []);

  const fetchReport = async () => {
    setLoading(true);
    try {
      const res = await reportApi.getAttendanceReport({
        start_date: startDate,
        end_date: endDate,
        department_id: selectedDept || undefined,
        status: selectedStatus || undefined,
      });
      if (res.success) {
        setReportRows(res.data);
      }
    } catch (err) {
      toast.error('Failed to generate attendance report');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReport();
  }, [startDate, endDate, selectedDept, selectedStatus]);

  const handleExport = async (format) => {
    setExporting(format);
    setDropdownOpen(false);
    try {
      const params = {
        start_date: startDate,
        end_date: endDate,
        ...(selectedDept ? { department_id: selectedDept } : {}),
        ...(selectedStatus ? { status: selectedStatus } : {}),
      };
      await reportApi.downloadReport(format, params);
      toast.success(`Exported report as ${format.toUpperCase()}`);
    } catch (err) {
      toast.error(`Failed to export report as ${format.toUpperCase()}`);
    } finally {
      setExporting(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Title & Multi-Format Export Options */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white tracking-tight">
            Attendance Reports & Multi-Format Export
          </h2>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Generate customized attendance statements and export to Excel, CSV, JSON, or Printable PDF
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2 flex-wrap">
          {/* Quick Excel Export */}
          <Button
            variant="primary"
            size="md"
            loading={exporting === 'excel'}
            onClick={() => handleExport('excel')}
            icon={FileSpreadsheet}
          >
            Export Excel (.xlsx)
          </Button>

          {/* Quick CSV Export */}
          <Button
            variant="outline"
            size="md"
            loading={exporting === 'csv'}
            onClick={() => handleExport('csv')}
            icon={Download}
          >
            Export CSV
          </Button>

          {/* More Formats Dropdown */}
          <div className="relative">
            <Button
              variant="outline"
              size="md"
              onClick={() => setDropdownOpen((prev) => !prev)}
            >
              <span>More Formats</span>
              <ChevronDown className="w-4 h-4 ml-1.5" />
            </Button>

            {dropdownOpen && (
              <div
                className="absolute right-0 mt-2 w-48 bg-white dark:bg-slate-900 rounded-xl shadow-xl border border-slate-200 dark:border-slate-800 py-1.5 z-50 animate-in fade-in zoom-in-95 duration-100"
                onClick={() => setDropdownOpen(false)}
              >
                <button
                  onClick={() => handleExport('excel')}
                  className="w-full px-4 py-2 text-left text-xs font-medium text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-800 flex items-center gap-2.5"
                >
                  <FileSpreadsheet className="w-4 h-4 text-emerald-600" />
                  <span>Microsoft Excel (.xlsx)</span>
                </button>

                <button
                  onClick={() => handleExport('csv')}
                  className="w-full px-4 py-2 text-left text-xs font-medium text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-800 flex items-center gap-2.5"
                >
                  <FileText className="w-4 h-4 text-blue-600" />
                  <span>CSV File (.csv)</span>
                </button>

                <button
                  onClick={() => handleExport('json')}
                  className="w-full px-4 py-2 text-left text-xs font-medium text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-800 flex items-center gap-2.5"
                >
                  <FileCode className="w-4 h-4 text-purple-600" />
                  <span>JSON Payload (.json)</span>
                </button>

                <div className="my-1 border-t border-slate-100 dark:border-slate-800" />

                <button
                  onClick={() => handleExport('html')}
                  className="w-full px-4 py-2 text-left text-xs font-medium text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-800 flex items-center gap-2.5"
                >
                  <Printer className="w-4 h-4 text-indigo-600" />
                  <span>Print / PDF View</span>
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Report Filter Controls */}
      <Card bodyClassName="p-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1.5">
              Start Date
            </label>
            <div className="flex items-center gap-2 bg-slate-50 dark:bg-slate-800 px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-700">
              <Calendar className="w-4 h-4 text-blue-600 dark:text-blue-400" />
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="bg-transparent border-none text-xs font-semibold text-slate-800 dark:text-slate-200 focus:outline-none w-full"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1.5">
              End Date
            </label>
            <div className="flex items-center gap-2 bg-slate-50 dark:bg-slate-800 px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-700">
              <Calendar className="w-4 h-4 text-blue-600 dark:text-blue-400" />
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="bg-transparent border-none text-xs font-semibold text-slate-800 dark:text-slate-200 focus:outline-none w-full"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1.5">
              Department
            </label>
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

          <div>
            <label className="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1.5">
              Status Filter
            </label>
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-xs font-medium rounded-xl px-3 py-2 text-slate-800 dark:text-slate-200 focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Attendance Statuses</option>
              {STATUS_OPTIONS.map((s) => (
                <option key={s.value} value={s.value}>
                  {s.label}
                </option>
              ))}
            </select>
          </div>
        </div>
      </Card>

      {/* Report Records Table */}
      <Card bodyClassName="p-0">
        {loading ? (
          <SkeletonLoader rows={8} type="table" />
        ) : reportRows.length === 0 ? (
          <EmptyState
            icon={FileSpreadsheet}
            title="No report records found"
            description="No attendance records were matched in the selected date range and filter criteria."
          />
        ) : (
          <div>
            <div className="px-6 py-4 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs text-slate-500">
              <span>Showing <strong className="text-slate-800 dark:text-slate-200">{reportRows.length}</strong> attendance statement records</span>
              <span>Range: {startDate} to {endDate}</span>
            </div>

            <Table
              headers={[
                'Employee Code',
                'Employee Name',
                'Department',
                'Date',
                'Status',
                'Check In',
                'Check Out',
                'Total Hours',
                'Overtime',
                'Late (Mins)',
                'Remarks'
              ]}
            >
              {reportRows.map((row, idx) => (
                <tr key={idx} className="hover:bg-slate-50/60 dark:hover:bg-slate-800/40 transition-colors">
                  <td className="py-3.5 px-4 pl-6 font-mono text-xs font-bold text-blue-600 dark:text-blue-400">
                    {row.employee_code}
                  </td>
                  <td className="py-3.5 px-4 font-semibold text-slate-900 dark:text-white">
                    {row.employee_name}
                  </td>
                  <td className="py-3.5 px-4 text-xs text-slate-500 dark:text-slate-400">
                    {row.department_name}
                  </td>
                  <td className="py-3.5 px-4 font-mono text-xs text-slate-600 dark:text-slate-300">
                    {row.attendance_date}
                  </td>
                  <td className="py-3.5 px-4">
                    <Badge variant={row.status} size="sm">
                      {row.status}
                    </Badge>
                  </td>
                  <td className="py-3.5 px-4 font-mono text-xs text-slate-600 dark:text-slate-300">
                    {row.check_in}
                  </td>
                  <td className="py-3.5 px-4 font-mono text-xs text-slate-600 dark:text-slate-300">
                    {row.check_out}
                  </td>
                  <td className="py-3.5 px-4 text-xs font-bold text-slate-800 dark:text-slate-200">
                    {row.total_hours}h
                  </td>
                  <td className="py-3.5 px-4 text-xs font-bold text-indigo-600 dark:text-indigo-400">
                    {row.overtime_hours > 0 ? `+${row.overtime_hours}h` : '-'}
                  </td>
                  <td className="py-3.5 px-4 text-xs font-mono text-slate-500">
                    {row.late_minutes > 0 ? `${row.late_minutes}m` : '-'}
                  </td>
                  <td className="py-3.5 px-4 pr-6 text-xs text-slate-500 dark:text-slate-400 max-w-xs truncate">
                    {row.remarks || '-'}
                  </td>
                </tr>
              ))}
            </Table>
          </div>
        )}
      </Card>
    </div>
  );
};
