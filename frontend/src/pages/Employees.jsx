import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { employeeApi } from '../api/employeeApi';
import { departmentApi } from '../api/departmentApi';
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
  Users,
  UserPlus,
  Search,
  Filter,
  Eye,
  Edit2,
  Trash2,
  CheckCircle,
  Clock,
  Building
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
  const [formData, setFormData] = useState({
    employee_id: '',
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    department_id: '',
    designation: '',
    joining_date: new Date().toISOString().split('T')[0],
    employment_type: 'FULL_TIME',
    status: 'ACTIVE',
    address: '',
    emergency_contact: '',
  });
  const [formLoading, setFormLoading] = useState(false);

  // Status Change Dialog
  const [statusTarget, setStatusTarget] = useState(null);
  const [newStatus, setNewStatus] = useState('');
  const [statusReason, setStatusReason] = useState('');
  const [statusLoading, setStatusLoading] = useState(false);

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
    setFormData({
      employee_id: '',
      first_name: '',
      last_name: '',
      email: '',
      phone: '',
      department_id: departments[0]?.id || '',
      designation: '',
      joining_date: new Date().toISOString().split('T')[0],
      employment_type: 'FULL_TIME',
      status: 'ACTIVE',
      address: '',
      emergency_contact: '',
    });
    setModalOpen(true);
  };

  const handleOpenEdit = (emp) => {
    setEditingEmployee(emp);
    setFormData({
      employee_id: emp.employee_id,
      first_name: emp.first_name,
      last_name: emp.last_name,
      email: emp.email,
      phone: emp.phone || '',
      department_id: emp.department_id,
      designation: emp.designation,
      joining_date: emp.joining_date,
      employment_type: emp.employment_type,
      status: emp.status,
      address: emp.address || '',
      emergency_contact: emp.emergency_contact || '',
    });
    setModalOpen(true);
  };

  const handleSubmitEmployee = async (e) => {
    e.preventDefault();
    setFormLoading(true);
    try {
      if (editingEmployee) {
        await employeeApi.updateEmployee(editingEmployee.id, formData);
        toast.success(`Employee ${formData.first_name} updated successfully`);
      } else {
        await employeeApi.createEmployee(formData);
        toast.success('New employee added successfully');
      }
      setModalOpen(false);
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

  return (
    <div className="space-y-6">
      {/* Title & Add Action */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white tracking-tight">
            Employee Directory
          </h2>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Manage organization staff, job designations, and employment statuses
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
              placeholder="Search by name, ID, or email..."
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
                'Employee',
                'ID',
                'Department',
                'Designation',
                'Joining Date',
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
                        {emp.first_name.charAt(0)}
                      </div>
                      <div>
                        <Link
                          to={`/employees/${emp.id}`}
                          className="font-semibold text-slate-900 dark:text-white hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
                        >
                          {emp.full_name}
                        </Link>
                        <div className="text-xs text-slate-400">{emp.email}</div>
                      </div>
                    </div>
                  </td>

                  <td className="py-3.5 px-4 font-mono text-xs font-medium text-slate-600 dark:text-slate-300">
                    {emp.employee_id}
                  </td>

                  <td className="py-3.5 px-4 text-xs text-slate-600 dark:text-slate-400">
                    {emp.department?.name || 'Unassigned'}
                  </td>

                  <td className="py-3.5 px-4 text-xs text-slate-600 dark:text-slate-400">
                    {emp.designation}
                  </td>

                  <td className="py-3.5 px-4 text-xs text-slate-500 font-mono">
                    {emp.joining_date}
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
        maxWidth="max-w-2xl"
        title={editingEmployee ? 'Edit Employee Details' : 'Add New Employee'}
        subtitle={
          editingEmployee
            ? `Updating profile for ${editingEmployee.full_name} (${editingEmployee.employee_id})`
            : 'Fill in employment and personal information'
        }
      >
        <form onSubmit={handleSubmitEmployee} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="First Name"
              required
              value={formData.first_name}
              onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
              placeholder="e.g. John"
            />
            <Input
              label="Last Name"
              required
              value={formData.last_name}
              onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
              placeholder="e.g. Doe"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="Email Address"
              type="email"
              required
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              placeholder="john.doe@company.com"
            />
            <Input
              label="Phone Number"
              value={formData.phone}
              onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
              placeholder="+1 (555) 000-0000"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Select
              label="Department"
              required
              value={formData.department_id}
              onChange={(e) => setFormData({ ...formData, department_id: Number(e.target.value) })}
              options={departments.map((d) => ({ value: d.id, label: d.name }))}
            />
            <Input
              label="Designation / Role"
              required
              value={formData.designation}
              onChange={(e) => setFormData({ ...formData, designation: e.target.value })}
              placeholder="e.g. Senior Software Engineer"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <Input
              label="Joining Date"
              type="date"
              required
              value={formData.joining_date}
              onChange={(e) => setFormData({ ...formData, joining_date: e.target.value })}
            />
            <Select
              label="Employment Type"
              value={formData.employment_type}
              onChange={(e) => setFormData({ ...formData, employment_type: e.target.value })}
              options={EMPLOYMENT_TYPES}
            />
            <Select
              label="Employment Status"
              value={formData.status}
              onChange={(e) => setFormData({ ...formData, status: e.target.value })}
              options={STATUS_OPTIONS}
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="Residential Address"
              value={formData.address}
              onChange={(e) => setFormData({ ...formData, address: e.target.value })}
              placeholder="City, State / Full address"
            />
            <Input
              label="Emergency Contact"
              value={formData.emergency_contact}
              onChange={(e) => setFormData({ ...formData, emergency_contact: e.target.value })}
              placeholder="Name & contact info"
            />
          </div>

          {!editingEmployee && (
            <Input
              label="Custom Employee Code (Optional)"
              value={formData.employee_id}
              onChange={(e) => setFormData({ ...formData, employee_id: e.target.value })}
              placeholder="Leave empty to auto-generate (e.g. EMP-0001)"
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
    </div>
  );
};
