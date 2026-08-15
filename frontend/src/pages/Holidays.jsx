import React, { useState, useEffect } from 'react';
import { holidayApi } from '../api/holidayApi';
import { useToast } from '../context/ToastContext';
import { useAuth } from '../context/AuthContext';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Input } from '../components/common/Input';
import { Badge } from '../components/common/Badge';
import { Modal } from '../components/common/Modal';
import { Table } from '../components/common/Table';
import { SkeletonLoader } from '../components/common/SkeletonLoader';
import { EmptyState } from '../components/common/EmptyState';
import { ConfirmDialog } from '../components/common/ConfirmDialog';
import { SunMedium, Plus, Edit2, Trash2, Calendar } from 'lucide-react';

export const Holidays = () => {
  const [holidays, setHolidays] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingHoliday, setEditingHoliday] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    date: new Date().toISOString().split('T')[0],
    description: '',
    is_active: true,
  });
  const [formLoading, setFormLoading] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [deleteLoading, setDeleteLoading] = useState(false);

  const { isAdmin } = useAuth();
  const toast = useToast();

  const fetchHolidays = async () => {
    setLoading(true);
    try {
      const res = await holidayApi.getHolidays();
      if (res.success) setHolidays(res.data);
    } catch (err) {
      toast.error('Failed to load holidays');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHolidays();
  }, []);

  const handleOpenCreate = () => {
    setEditingHoliday(null);
    setFormData({
      name: '',
      date: new Date().toISOString().split('T')[0],
      description: '',
      is_active: true,
    });
    setModalOpen(true);
  };

  const handleOpenEdit = (hol) => {
    setEditingHoliday(hol);
    setFormData({
      name: hol.name,
      date: hol.date,
      description: hol.description || '',
      is_active: hol.is_active,
    });
    setModalOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setFormLoading(true);
    try {
      if (editingHoliday) {
        await holidayApi.updateHoliday(editingHoliday.id, formData);
        toast.success(`Holiday '${formData.name}' updated`);
      } else {
        await holidayApi.createHoliday(formData);
        toast.success(`Holiday '${formData.name}' scheduled`);
      }
      setModalOpen(false);
      fetchHolidays();
    } catch (err) {
      toast.error(err.response?.data?.message || 'Failed to save holiday');
    } finally {
      setFormLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    setDeleteLoading(true);
    try {
      await holidayApi.deleteHoliday(deleteTarget.id);
      toast.success(`Holiday '${deleteTarget.name}' deleted`);
      setDeleteTarget(null);
      fetchHolidays();
    } catch (err) {
      toast.error('Failed to delete holiday');
    } finally {
      setDeleteLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white tracking-tight">
            Company Holidays
          </h2>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Configure paid annual and gazetted holidays reflected on attendance sheets
          </p>
        </div>

        <Button variant="primary" size="md" onClick={handleOpenCreate} icon={Plus}>
          Add Holiday
        </Button>
      </div>

      <Card bodyClassName="p-0">
        {loading ? (
          <SkeletonLoader rows={5} type="table" />
        ) : holidays.length === 0 ? (
          <EmptyState
            icon={SunMedium}
            title="No holidays scheduled"
            description="Add company holidays so they automatically populate as non-working days."
            actionLabel="Add Holiday"
            onAction={handleOpenCreate}
          />
        ) : (
          <Table headers={['Holiday Name', 'Date', 'Day of Week', 'Description', 'Status', { label: 'Actions', align: 'right' }]}>
            {holidays.map((hol) => {
              const dayName = new Date(hol.date).toLocaleDateString('en-US', { weekday: 'long' });
              return (
                <tr key={hol.id} className="hover:bg-slate-50/60 dark:hover:bg-slate-800/40 transition-colors">
                  <td className="py-3.5 px-4 pl-6 font-semibold text-slate-900 dark:text-white">
                    {hol.name}
                  </td>
                  <td className="py-3.5 px-4 text-xs font-mono text-blue-600 dark:text-blue-400 font-semibold">
                    {hol.date}
                  </td>
                  <td className="py-3.5 px-4 text-xs text-slate-500">
                    {dayName}
                  </td>
                  <td className="py-3.5 px-4 text-xs text-slate-500 dark:text-slate-400 max-w-xs">
                    {hol.description || '-'}
                  </td>
                  <td className="py-3.5 px-4">
                    <Badge variant={hol.is_active ? 'HOLIDAY' : 'INACTIVE'} size="sm" dot>
                      {hol.is_active ? 'Active' : 'Disabled'}
                    </Badge>
                  </td>
                  <td className="py-3.5 px-4 pr-6 text-right">
                    <div className="flex items-center justify-end gap-1.5">
                      <Button variant="ghost" size="sm" icon={Edit2} onClick={() => handleOpenEdit(hol)}>
                        Edit
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-rose-600 hover:text-rose-700 hover:bg-rose-50 dark:hover:bg-rose-950"
                        icon={Trash2}
                        onClick={() => setDeleteTarget(hol)}
                      >
                        Delete
                      </Button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </Table>
        )}
      </Card>

      {/* Add / Edit Modal */}
      <Modal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        title={editingHoliday ? 'Edit Holiday' : 'Add Holiday'}
        subtitle={editingHoliday ? `Updating '${editingHoliday.name}'` : 'Schedule a new company-wide holiday'}
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Holiday Title"
            required
            placeholder="e.g. Labor Day"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
          />

          <Input
            label="Date"
            type="date"
            required
            value={formData.date}
            onChange={(e) => setFormData({ ...formData, date: e.target.value })}
          />

          <Input
            label="Description"
            placeholder="Brief holiday details"
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
          />

          <div className="flex items-center gap-2 pt-2">
            <input
              type="checkbox"
              id="hol_active"
              checked={formData.is_active}
              onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
              className="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
            />
            <label htmlFor="hol_active" className="text-xs font-medium text-slate-700 dark:text-slate-300">
              Holiday is active
            </label>
          </div>

          <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-100 dark:border-slate-800">
            <Button variant="outline" size="md" onClick={() => setModalOpen(false)} disabled={formLoading}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" size="md" loading={formLoading}>
              {editingHoliday ? 'Save Changes' : 'Schedule Holiday'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Confirm Delete Dialog */}
      <ConfirmDialog
        isOpen={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleDelete}
        loading={deleteLoading}
        title="Delete Holiday"
        message={`Are you sure you want to remove '${deleteTarget?.name}' (${deleteTarget?.date}) from scheduled holidays?`}
        confirmText="Delete"
        variant="danger"
      />
    </div>
  );
};
