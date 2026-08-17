import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { employeeApi } from '../api/employeeApi';
import { departmentApi } from '../api/departmentApi';
import { useToast } from '../context/ToastContext';
import { useAuth } from '../context/AuthContext';
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
  Users,
  UserPlus,
  Search,
  Filter,
  Eye,
  Edit2,
  Trash2,
  CheckCircle,
  Clock,
  Building,
  Phone,
  PlusCircle,
  ShieldAlert
} from 'lucide-react';

const STATUS_OPTIONS = [
  { value: 'ACTIVE', label: 'Active' },
  { value: 'INACTIVE', label: 'Inactive' },
  { value: 'RESIGNED', label: 'Resigned' },
  { value: 'TERMINATED', label: 'Terminated' },
  { value: 'ON_NOTICE', label: 'On Notice' },
];

const EMPLOYMENT_TYPES = [
  { value: 'FULL_TIME', label: 'Full Time' },
  { value: 'PART_TIME', label: 'Part Time' },
  { value: 'CONTRACT', label: 'Contract' },
  { value: 'INTERN', label: 'Intern' },
];

export const Employees = () => {
  const { isAdmin } = useAuth();
  const [employees, setEmployees] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);

  // Filters
  const [search, setSearch] = useState('');
  const [selectedDept, setSelectedDept] = useState('');
  const [selectedStatus, setSelectedStatus] = useState('');
  const [departments, setDepartments] = useState([]);

  // Create / Edit Modal
  const [modalOpen, setModalOpen] = useState(false);
  const [editingEmployee, setEditingEmployee] = useState(null);
  const [isOtherDept, setIsOtherDept] = useState(false);
  const [formData, setFormData] = useState({
    employee_id: '',
    first_name: '',
    phone: '',
    department_id: '',
    new_department_name: '',
    designation: 'Staff',
    employment_type: 'FULL_TIME',
    status: 'ACTIVE',
  });
  const [formLoading, setFormLoading] = useState(false);

  // Status Change Dialog
  const [statusTarget, setStatusTarget] = useState(null);
  const [newStatus, setNewStatus] = useState('');
  const [statusReason, setStatusReason] = useState('');
  const [statusLoading, setStatusLoading] = useState(false);

  // Admin Delete Dialog
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [deleteLoading, setDeleteLoading] = useState(false);

  const toast = useToast();

  const fetchDepts = async () => {
    try {
      const res = await departmentApi.getDepartments(true);
      if (res.success) setDepartments(res.data);
    } catch (err) {}
  };

  useEffect(() => {
    fetchDepts();
  }, []);

  const fetchEmployees = async () => {
    setLoading(true);
    try {
      const res = await employeeApi.getEmployees({
        page,
        page_size: 15,
        search: search.trim() || undefined,
        department_id: selectedDept || undefined,
        status_filter: selectedStatus || undefined,
      });
      if (res.success && res.data) {
        setEmployees(res.data.items);
        setTotal(res.data.total);
        setTotalPages(res.data.total_pages);
      }
    } catch (err) {
      toast.error('Failed to load employees list');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEmployees();
  }, [page, selectedDept, selectedStatus]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setPage(1);
    fetchEmployees();
  };

  const handleOpenCreate = () => {
    setEditingEmployee(null);
    setIsOtherDept(false);
    setFormData({
      employee_id: '',
      first_name: '',
      phone: '',
      department_id: departments[0]?.id || '',
      new_department_name: '',
      designation: 'Staff',
      joining_date: new Date().toISOString().split('T')[0],
      employment_type: 'FULL_TIME',
      status: 'ACTIVE',
    });
    setModalOpen(true);
  };

  const handleOpenEdit = (emp) => {
    setEditingEmployee(emp);
    setIsOtherDept(false);
    setFormData({
      employee_id: emp.employee_id,
      first_name: emp.first_name || emp.full_name,
      phone: emp.phone || '',
      department_id: emp.department_id || '',
      new_department_name: '',
      designation: emp.designation || 'Staff',
      joining_date: emp.joining_date || new Date().toISOString().split('T')[0],
      employment_type: emp.employment_type || 'FULL_TIME',
      status: emp.status || 'ACTIVE',
    });
    setModalOpen(true);
  };

  const handleDeptSelectChange = (e) => {
    const val = e.target.value;
    if (val === '__OTHER__') {
      setIsOtherDept(true);
      setFormData({ ...formData, department_id: '', new_department_name: '' });
    } else {
      setIsOtherDept(false);
      setFormData({ ...formData, department_id: Number(val), new_department_name: '' });
    }
  };

  const handleSubmitEmployee = async (e) => {
    e.preventDefault();
    setFormLoading(true);
    try {
      const payload = {
        employee_id: formData.employee_id.trim() || undefined,
        first_name: formData.first_name.trim(),
        phone: formData.phone.trim() || undefined,
        department_id: formData.department_id ? Number(formData.department_id) : undefined,
        new_department_name: isOtherDept && formData.new_department_name.trim() ? formData.new_department_name.trim() : undefined,
        designation: formData.designation.trim() || 'Staff',
        joining_date: formData.joining_date || undefined,
        employment_type: formData.employment_type,
        status: formData.status,
      };

      if (editingEmployee) {
        await employeeApi.updateEmployee(editingEmployee.id, payload);
        toast.success(`Employee ${formData.first_name} updated successfully`);
      } else {
        await employeeApi.createEmployee(payload);
        toast.success('New employee added successfully');
      }
      setModalOpen(false);
      fetchDepts(); // Refresh departments in case a new one was added
      fetchEmployees();
    } catch (err) {
      toast.error(err.response?.data?.message || 'Failed to save employee details');
    } finally {
      setFormLoading(false);
    }
  };

  const handleStatusChangeSubmit = async () => {
    if (!statusTarget || !newStatus) return;
    setStatusLoading(true);
    try {
      await employeeApi.updateStatus(statusTarget.id, newStatus, statusReason);
      toast.success(`Updated status for ${statusTarget.full_name} to ${newStatus}`);
      setStatusTarget(null);
      fetchEmployees();
    } catch (err) {
      toast.error(err.response?.data?.message || 'Failed to update status');
    } finally {
      setStatusLoading(false);
    }
  };

  const handleDeleteEmployee = async () => {
    if (!deleteTarget) return;
    setDeleteLoading(true);
    try {
      await employeeApi.deleteEmployee(deleteTarget.id);
      toast.success(`Employee ${deleteTarget.full_name || deleteTarget.first_name} deleted successfully`);
      setDeleteTarget(null);
      fetchEmployees();
    } catch (err) {
      toast.error(err.response?.data?.message || 'Failed to delete employee');
    } finally {
      setDeleteLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Title & Add Action */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white tracking-tight">
            Employee Directory
          </h2>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Manage organization staff, job designations, and instant department assignments
          </p>
        </div>

        <Button
          variant="primary"
          size="md"
          onClick={handleOpenCreate}
          icon={UserPlus}
        >
          Add Employee
        </Button>
      </div>

      {/* Filter Bar */}
      <Card bodyClassName="p-4">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          <form onSubmit={handleSearchSubmit} className="relative w-full sm:w-80">
            <input
              type="text"
              placeholder="Search by name, employee code, or phone..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-xs rounded-xl pl-9 pr-4 py-2.5 text-slate-800 dark:text-slate-200 focus:ring-2 focus:ring-blue-500"
            />
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
          </form>

          <div className="flex flex-wrap items-center gap-3 w-full sm:w-auto">
            <select
              value={selectedDept}
              onChange={(e) => {
                setSelectedDept(e.target.value);
                setPage(1);
              }}
              className="bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-xs font-medium rounded-xl px-3 py-2 text-slate-800 dark:text-slate-200 focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Departments</option>
              {departments.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name}
                </option>
              ))}
            </select>

            <select
              value={selectedStatus}
              onChange={(e) => {
                setSelectedStatus(e.target.value);
                setPage(1);
              }}
              className="bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-xs font-medium rounded-xl px-3 py-2 text-slate-800 dark:text-slate-200 focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Statuses</option>
              {STATUS_OPTIONS.map((s) => (
                <option key={s.value} value={s.value}>
                  {s.label}
                </option>
              ))}
            </select>
          </div>
        </div>
      </Card>

      {/* Employees Table Card */}
      <Card bodyClassName="p-0">
        {loading ? (
          <SkeletonLoader rows={6} type="table" />
        ) : employees.length === 0 ? (
          <EmptyState
            icon={Users}
            title="No employees found"
            description="No employee records matched your filter criteria."
            actionLabel="Add Employee"
            onAction={handleOpenCreate}
          />
        ) : (
          <div>
            <Table
              headers={[
                'Employee Name',
                'Employee ID',
                'Department',
                'Designation',
                'Contact Number',
                'Status',
                { label: 'Actions', align: 'right' },
              ]}
            >
              {employees.map((emp) => (
                <tr
                  key={emp.id}
                  className="hover:bg-slate-50/60 dark:hover:bg-slate-800/40 transition-colors"
                >
                  <td className="py-3.5 px-4 pl-6">
                    <div className="flex items-center gap-3">
                      <div className="w-9 h-9 rounded-full bg-blue-100 dark:bg-blue-950 text-blue-700 dark:text-blue-300 flex items-center justify-center font-bold text-xs shrink-0">
                        {emp.first_name ? emp.first_name.charAt(0).toUpperCase() : 'E'}
                      </div>
                      <div>
                        <Link
                          to={`/employees/${emp.id}`}
                          className="font-semibold text-slate-900 dark:text-white hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
                        >
                          {emp.full_name || emp.first_name}
                        </Link>
                      </div>
                    </div>
                  </td>

                  <td className="py-3.5 px-4 font-mono text-xs font-medium text-slate-600 dark:text-slate-300">
                    {emp.employee_id}
                  </td>

                  <td className="py-3.5 px-4 text-xs text-slate-600 dark:text-slate-400 font-medium">
                    {emp.department?.name || 'Unassigned'}
                  </td>

                  <td className="py-3.5 px-4 text-xs text-slate-600 dark:text-slate-400">
                    {emp.designation || 'Staff'}
                  </td>

                  <td className="py-3.5 px-4 text-xs font-mono text-slate-500">
                    {emp.phone || '-'}
                  </td>

                  <td className="py-3.5 px-4">
                    <button
                      onClick={() => {
                        setStatusTarget(emp);
                        setNewStatus(emp.status);
                        setStatusReason('');
                      }}
                      className="cursor-pointer hover:opacity-80 transition-opacity"
                    >
                      <Badge variant={emp.status} size="sm" dot>
                        {emp.status}
                      </Badge>
                    </button>
                  </td>

                  <td className="py-3.5 px-4 pr-6 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <Link to={`/employees/${emp.id}`}>
                        <Button variant="ghost" size="sm" icon={Eye}>
                          Profile
                        </Button>
                      </Link>
                      <Button
                        variant="ghost"
                        size="sm"
                        icon={Edit2}
                        onClick={() => handleOpenEdit(emp)}
                      >
                        Edit
                      </Button>
                      {isAdmin && (
                        <Button
                          variant="ghost"
                          size="sm"
                          icon={Trash2}
                          className="text-rose-600 hover:text-rose-700 hover:bg-rose-50 dark:hover:bg-rose-950/40"
                          onClick={() => setDeleteTarget(emp)}
                        >
                          Delete
                        </Button>
                      )}
                    </div>
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

      {/* Add / Edit Employee Modal */}
      <Modal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        maxWidth="max-w-xl"
        title={editingEmployee ? 'Edit Employee' : 'Add Employee'}
        subtitle={
          editingEmployee
            ? `Updating profile for ${editingEmployee.full_name || editingEmployee.first_name} (${editingEmployee.employee_id})`
            : 'Fill in the required information to register a staff member'
        }
      >
        <form onSubmit={handleSubmitEmployee} className="space-y-4">
          {/* Employee Name */}
          <Input
            label="Employee Name"
            required
            value={formData.first_name}
            onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
            placeholder="e.g. Rajesh Kumar"
          />

          {/* Contact (Optional) */}
          <Input
            label="Contact Number (Optional)"
            type="tel"
            value={formData.phone}
            onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
            placeholder="e.g. +91 98765 43210"
            helperText="Optional mobile or phone number"
          />

          {/* Department Selection with Instant "Other" Creation */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
              Department
            </label>
            <select
              value={isOtherDept ? '__OTHER__' : (formData.department_id || '')}
              onChange={handleDeptSelectChange}
              className="w-full bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 text-xs font-medium rounded-xl px-3 py-2.5 text-slate-800 dark:text-slate-200 focus:ring-2 focus:ring-blue-500"
            >
              <option value="">-- Select Department --</option>
              {departments.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name}
                </option>
              ))}
              <option value="__OTHER__" className="font-bold text-blue-600 dark:text-blue-400">
                + Other (Create New Department...)
              </option>
            </select>
          </div>

          {/* Instant Department Name Input if "Other" Selected */}
          {isOtherDept && (
            <div className="p-3.5 rounded-xl bg-blue-50/60 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-800 animate-in fade-in duration-150">
              <Input
                label="New Department Name"
                required
                value={formData.new_department_name}
                onChange={(e) => setFormData({ ...formData, new_department_name: e.target.value })}
                placeholder="e.g. Quality Assurance"
                helperText="This new department will be automatically created and assigned."
              />
            </div>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="Designation / Role"
              value={formData.designation}
              onChange={(e) => setFormData({ ...formData, designation: e.target.value })}
              placeholder="e.g. Software Engineer, Supervisor"
            />
            <Select
              label="Employment Type"
              value={formData.employment_type}
              onChange={(e) => setFormData({ ...formData, employment_type: e.target.value })}
              options={EMPLOYMENT_TYPES}
            />
          </div>

          <div>
            <Select
              label="Employment Status"
              value={formData.status}
              onChange={(e) => setFormData({ ...formData, status: e.target.value })}
              options={STATUS_OPTIONS}
            />
          </div>

          {!editingEmployee && (
            <Input
              label="Custom Employee Code (Optional)"
              value={formData.employee_id}
              onChange={(e) => setFormData({ ...formData, employee_id: e.target.value })}
              placeholder="Leave blank to auto-generate (e.g. EMP-0001)"
              helperText="Auto-assigned sequentially if left blank"
            />
          )}

          <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-100 dark:border-slate-800">
            <Button
              variant="outline"
              size="md"
              onClick={() => setModalOpen(false)}
              disabled={formLoading}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              size="md"
              loading={formLoading}
            >
              {editingEmployee ? 'Save Changes' : 'Create Employee'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Change Status Modal */}
      <Modal
        isOpen={!!statusTarget}
        onClose={() => setStatusTarget(null)}
        title="Update Employment Status"
        subtitle={`Changing status for ${statusTarget?.full_name} (${statusTarget?.employee_id})`}
      >
        <div className="space-y-4">
          <Select
            label="New Status"
            value={newStatus}
            onChange={(e) => setNewStatus(e.target.value)}
            options={STATUS_OPTIONS}
            required
          />

          <Input
            label="Reason for Change"
            placeholder="e.g. Resignation accepted, notice period started"
            value={statusReason}
            onChange={(e) => setStatusReason(e.target.value)}
            helperText="Recorded permanently in the system audit log."
          />

          <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-100 dark:border-slate-800">
            <Button
              variant="outline"
              size="md"
              onClick={() => setStatusTarget(null)}
              disabled={statusLoading}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              size="md"
              loading={statusLoading}
              onClick={handleStatusChangeSubmit}
            >
              Update Status
            </Button>
          </div>
        </div>
      </Modal>

      {/* Delete Employee Confirmation Dialog (Admin Only) */}
      <ConfirmDialog
        isOpen={!!deleteTarget}
        title="Delete Employee"
        message={`Are you sure you want to delete ${deleteTarget?.full_name || deleteTarget?.first_name} (${deleteTarget?.employee_id})? This will remove their record from active directory while preserving audit and attendance history.`}
        confirmLabel="Delete Employee"
        confirmVariant="danger"
        loading={deleteLoading}
        onCancel={() => setDeleteTarget(null)}
        onConfirm={handleDeleteEmployee}
      />
    </div>
  );
};
