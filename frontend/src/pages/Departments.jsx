import React, { useState, useEffect } from 'react';
import { departmentApi } from '../api/departmentApi';
import { useToast } from '../context/ToastContext';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Input } from '../components/common/Input';
import { Badge } from '../components/common/Badge';
import { Modal } from '../components/common/Modal';
import { Table } from '../components/common/Table';
import { SkeletonLoader } from '../components/common/SkeletonLoader';
import { EmptyState } from '../components/common/EmptyState';
import { ConfirmDialog } from '../components/common/ConfirmDialog';
import { Building2, Plus, Edit2, Trash2, Users } from 'lucide-react';

export const Departments = () => {
  const [departments, setDepartments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingDept, setEditingDept] = useState(null);
  const [formData, setFormData] = useState({ name: '', description: '', is_active: true });
  const [formLoading, setFormLoading] = useState(false);

  // Delete dialog
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [deleteLoading, setDeleteLoading] = useState(false);

  const toast = useToast();

  const fetchDepartments = async () => {
    setLoading(true);
    try {
      const res = await departmentApi.getDepartments(false);
      if (res.success) setDepartments(res.data);
    } catch (err) {
      toast.error('Failed to load departments');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDepartments();
  }, []);

  const handleOpenCreate = () => {
    setEditingDept(null);
    setFormData({ name: '', description: '', is_active: true });
    setModalOpen(true);
  };

  const handleOpenEdit = (dept) => {
    setEditingDept(dept);
    setFormData({ name: dept.name, description: dept.description || '', is_active: dept.is_active });
    setModalOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.name.trim()) {
      toast.error('Department name is required');
      return;
    }

    setFormLoading(true);
    try {
      if (editingDept) {
        await departmentApi.updateDepartment(editingDept.id, formData);
        toast.success(`Department '${formData.name}' updated`);
      } else {
        await departmentApi.createDepartment(formData);
        toast.success(`Department '${formData.name}' created`);
      }
      setModalOpen(false);
      fetchDepartments();
    } catch (err) {
      toast.error(err.response?.data?.message || 'Failed to save department');
    } finally {
      setFormLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    setDeleteLoading(true);
    try {
      await departmentApi.deleteDepartment(deleteTarget.id);
      toast.success(`Department '${deleteTarget.name}' deleted`);
      setDeleteTarget(null);
      fetchDepartments();
    } catch (err) {
      toast.error(err.response?.data?.message || 'Failed to delete department');
    } finally {
      setDeleteLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white tracking-tight">
            Departments
          </h2>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Organize company divisions, manage team structures, and track staff counts
          </p>
        </div>

        <Button variant="primary" size="md" onClick={handleOpenCreate} icon={Plus}>
          New Department
        </Button>
      </div>

      <Card bodyClassName="p-0">
        {loading ? (
          <SkeletonLoader rows={5} type="table" />
        ) : departments.length === 0 ? (
          <EmptyState
            icon={Building2}
            title="No departments created yet"
            description="Create departments to group employees and structure attendance workflows."
            actionLabel="Create Department"
            onAction={handleOpenCreate}
          />
        ) : (
          <Table headers={['Department Name', 'Description', 'Total Staff', 'Status', { label: 'Actions', align: 'right' }]}>
            {departments.map((dept) => (
              <tr key={dept.id} className="hover:bg-slate-50/60 dark:hover:bg-slate-800/40 transition-colors">
                <td className="py-3.5 px-4 pl-6 font-semibold text-slate-900 dark:text-white">
                  {dept.name}
                </td>
                <td className="py-3.5 px-4 text-xs text-slate-500 dark:text-slate-400 max-w-sm">
                  {dept.description || '-'}
                </td>
                <td className="py-3.5 px-4">
                  <div className="inline-flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-lg bg-blue-50 text-blue-700 dark:bg-blue-950 dark:text-blue-300">
                    <Users className="w-3.5 h-3.5" />
                    <span>{dept.employee_count} staff</span>
                  </div>
                </td>
                <td className="py-3.5 px-4">
                  <Badge variant={dept.is_active ? 'ACTIVE' : 'INACTIVE'} size="sm" dot>
                    {dept.is_active ? 'Active' : 'Inactive'}
                  </Badge>
                </td>
                <td className="py-3.5 px-4 pr-6 text-right">
                  <div className="flex items-center justify-end gap-1.5">
                    <Button variant="ghost" size="sm" icon={Edit2} onClick={() => handleOpenEdit(dept)}>
                      Edit
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-rose-600 hover:text-rose-700 hover:bg-rose-50 dark:hover:bg-rose-950"
                      icon={Trash2}
                      onClick={() => setDeleteTarget(dept)}
                    >
                      Delete
                    </Button>
                  </div>
                </td>
              </tr>
            ))}
          </Table>
        )}
      </Card>

      {/* Create / Edit Modal */}
      <Modal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        title={editingDept ? 'Edit Department' : 'Create Department'}
        subtitle={editingDept ? `Modifying '${editingDept.name}'` : 'Add a new organizational department'}
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Department Name"
            required
            placeholder="e.g. Quality Assurance"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
          />

          <Input
            label="Description"
            placeholder="Brief description of department roles"
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
          />

          <div className="flex items-center gap-2 pt-2">
            <input
              type="checkbox"
              id="is_active"
              checked={formData.is_active}
              onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
              className="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
            />
            <label htmlFor="is_active" className="text-xs font-medium text-slate-700 dark:text-slate-300">
              Department is active
            </label>
          </div>

          <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-100 dark:border-slate-800">
            <Button variant="outline" size="md" onClick={() => setModalOpen(false)} disabled={formLoading}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" size="md" loading={formLoading}>
              {editingDept ? 'Save Changes' : 'Create Department'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        isOpen={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleDelete}
        loading={deleteLoading}
        title="Delete Department"
        message={`Are you sure you want to delete department '${deleteTarget?.name}'? Note: Departments with assigned employees cannot be deleted.`}
        confirmText="Delete"
        variant="danger"
      />
    </div>
  );
};
