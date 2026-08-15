import React, { useState, useEffect } from 'react';
import { userApi } from '../api/index';
import { useToast } from '../context/ToastContext';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Input } from '../components/common/Input';
import { Select } from '../components/common/Select';
import { Badge } from '../components/common/Badge';
import { Modal } from '../components/common/Modal';
import { Table } from '../components/common/Table';
import { SkeletonLoader } from '../components/common/SkeletonLoader';
import { EmptyState } from '../components/common/EmptyState';
import { UserCheck, Plus, Edit2, Shield, Lock, Mail, User } from 'lucide-react';

export const UsersPage = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    full_name: '',
    role: 'MANAGER',
    password: '',
    is_active: true,
  });
  const [formLoading, setFormLoading] = useState(false);

  const toast = useToast();

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const res = await userApi.getUsers();
      if (res.success) setUsers(res.data);
    } catch (err) {
      toast.error('Failed to load user accounts');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const handleOpenCreate = () => {
    setEditingUser(null);
    setFormData({
      username: '',
      email: '',
      full_name: '',
      role: 'MANAGER',
      password: '',
      is_active: true,
    });
    setModalOpen(true);
  };

  const handleOpenEdit = (u) => {
    setEditingUser(u);
    setFormData({
      username: u.username,
      email: u.email,
      full_name: u.full_name,
      role: u.role,
      password: '',
      is_active: u.is_active,
    });
    setModalOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setFormLoading(true);
    try {
      if (editingUser) {
        await userApi.updateUser(editingUser.id, {
          email: formData.email,
          full_name: formData.full_name,
          role: formData.role,
          is_active: formData.is_active,
        });
        toast.success(`User ${formData.username} updated`);
      } else {
        if (!formData.password || formData.password.length < 8) {
          toast.error('Password must be at least 8 characters');
          setFormLoading(false);
          return;
        }
        await userApi.createUser(formData);
        toast.success(`User account for ${formData.username} created`);
      }
      setModalOpen(false);
      fetchUsers();
    } catch (err) {
      toast.error(err.response?.data?.message || 'Failed to save user account');
    } finally {
      setFormLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white tracking-tight">
            User Accounts & RBAC
          </h2>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Manage administrative credentials, system managers, and role assignments
          </p>
        </div>

        <Button variant="primary" size="md" onClick={handleOpenCreate} icon={Plus}>
          New User Account
        </Button>
      </div>

      <Card bodyClassName="p-0">
        {loading ? (
          <SkeletonLoader rows={4} type="table" />
        ) : users.length === 0 ? (
          <EmptyState
            icon={UserCheck}
            title="No user accounts found"
            actionLabel="Create User"
            onAction={handleOpenCreate}
          />
        ) : (
          <Table headers={['User', 'Username', 'Email', 'Role', 'Status', 'Last Login', { label: 'Actions', align: 'right' }]}>
            {users.map((u) => (
              <tr key={u.id} className="hover:bg-slate-50/60 dark:hover:bg-slate-800/40 transition-colors">
                <td className="py-3.5 px-4 pl-6">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-950 text-blue-700 dark:text-blue-300 flex items-center justify-center font-bold text-xs shrink-0">
                      {u.full_name.charAt(0)}
                    </div>
                    <span className="font-semibold text-slate-900 dark:text-white">
                      {u.full_name}
                    </span>
                  </div>
                </td>

                <td className="py-3.5 px-4 font-mono text-xs font-semibold text-slate-700 dark:text-slate-300">
                  {u.username}
                </td>

                <td className="py-3.5 px-4 text-xs text-slate-500">
                  {u.email}
                </td>

                <td className="py-3.5 px-4">
                  <span className={`inline-block text-[11px] font-bold px-2 py-0.5 rounded-full border ${
                    u.role === 'ADMIN'
                      ? 'bg-purple-50 text-purple-700 border-purple-200 dark:bg-purple-950/60 dark:text-purple-300 dark:border-purple-800'
                      : 'bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-950/60 dark:text-blue-300 dark:border-blue-800'
                  }`}>
                    {u.role}
                  </span>
                </td>

                <td className="py-3.5 px-4">
                  <Badge variant={u.is_active ? 'ACTIVE' : 'INACTIVE'} size="sm" dot>
                    {u.is_active ? 'Active' : 'Disabled'}
                  </Badge>
                </td>

                <td className="py-3.5 px-4 text-xs text-slate-400 font-mono">
                  {u.last_login ? new Date(u.last_login).toLocaleString() : 'Never'}
                </td>

                <td className="py-3.5 px-4 pr-6 text-right">
                  <Button variant="ghost" size="sm" icon={Edit2} onClick={() => handleOpenEdit(u)}>
                    Edit
                  </Button>
                </td>
              </tr>
            ))}
          </Table>
        )}
      </Card>

      {/* User Modal */}
      <Modal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        title={editingUser ? 'Edit User Account' : 'Create User Account'}
        subtitle={editingUser ? `Updating account for '${editingUser.username}'` : 'Provide credentials and role'}
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="Username"
              required
              disabled={!!editingUser}
              placeholder="e.g. jdoe"
              value={formData.username}
              onChange={(e) => setFormData({ ...formData, username: e.target.value })}
            />
            <Input
              label="Full Name"
              required
              placeholder="e.g. John Doe"
              value={formData.full_name}
              onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="Email Address"
              type="email"
              required
              placeholder="john@company.com"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            />
            <Select
              label="Role"
              required
              value={formData.role}
              onChange={(e) => setFormData({ ...formData, role: e.target.value })}
              options={[
                { value: 'MANAGER', label: 'Manager (Attendance & Leaves)' },
                { value: 'ADMIN', label: 'Administrator (Full Access)' },
              ]}
            />
          </div>

          {!editingUser && (
            <Input
              label="Initial Password"
              type="password"
              required
              placeholder="Min 8 characters"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
            />
          )}

          <div className="flex items-center gap-2 pt-2">
            <input
              type="checkbox"
              id="user_active"
              checked={formData.is_active}
              onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
              className="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
            />
            <label htmlFor="user_active" className="text-xs font-medium text-slate-700 dark:text-slate-300">
              User account is active
            </label>
          </div>

          <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-100 dark:border-slate-800">
            <Button variant="outline" size="md" onClick={() => setModalOpen(false)} disabled={formLoading}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" size="md" loading={formLoading}>
              {editingUser ? 'Save Changes' : 'Create User'}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
