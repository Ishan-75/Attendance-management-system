import React, { useState, useEffect } from 'react';
import { settingApi } from '../api/settingApi';
import { systemApi } from '../api/systemApi';
import { useToast } from '../context/ToastContext';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Input } from '../components/common/Input';
import { SkeletonLoader } from '../components/common/SkeletonLoader';
import { Settings as SettingsIcon, Clock, Calendar, Save, ShieldCheck, Mail, Send, CheckCircle2, AlertCircle } from 'lucide-react';

export const Settings = () => {
  const [settings, setSettings] = useState({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  // SMTP state
  const [smtpStatus, setSmtpStatus] = useState(null);
  const [testingEmail, setTestingEmail] = useState(false);
  const [testEmailTarget, setTestEmailTarget] = useState('attendancesystem55@gmail.com');

  const toast = useToast();

  const fetchSettings = async () => {
    setLoading(true);
    try {
      const res = await settingApi.getSettings();
      if (res.success && res.data) {
        const dict = {};
        res.data.forEach((s) => {
          dict[s.key] = s.value;
        });
        setSettings(dict);
      }

      // Fetch SMTP status
      try {
        const smtpRes = await systemApi.getSmtpStatus();
        if (smtpRes.success) {
          setSmtpStatus(smtpRes.data);
        }
      } catch (e) {
        // non-critical
      }
    } catch (err) {
      toast.error('Failed to load system settings');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSettings();
  }, []);

  const handleChange = (key, value) => {
    setSettings((prev) => ({ ...prev, [key]: value }));
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      const payload = Object.keys(settings).map((k) => ({
        key: k,
        value: String(settings[k]),
      }));
      await settingApi.updateSettings(payload);
      toast.success('System attendance rules and configurations updated');
      fetchSettings();
    } catch (err) {
      toast.error(err.response?.data?.message || 'Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  const handleSendTestEmail = async () => {
    setTestingEmail(true);
    try {
      const res = await systemApi.testEmail(testEmailTarget);
      if (res.success) {
        toast.success(res.message || 'Test email dispatched successfully');
      } else {
        toast.error(res.message || 'Failed to send test email');
      }
    } catch (err) {
      toast.error(err.response?.data?.message || 'Failed to dispatch test email');
    } finally {
      setTestingEmail(false);
    }
  };

  const daysOfWeek = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

  const isWeeklyOff = (dayName) => {
    const offs = (settings['weekly_off_days'] || '').split(',').map((d) => d.trim().toLowerCase());
    return offs.includes(dayName.toLowerCase());
  };

  const toggleWeeklyOff = (dayName) => {
    const offs = (settings['weekly_off_days'] || '')
      .split(',')
      .map((d) => d.trim().toLowerCase())
      .filter(Boolean);

    const target = dayName.toLowerCase();
    let newOffs;
    if (offs.includes(target)) {
      newOffs = offs.filter((d) => d !== target);
    } else {
      newOffs = [...offs, target];
    }
    handleChange('weekly_off_days', newOffs.join(','));
  };

  if (loading) {
    return <SkeletonLoader rows={6} type="table" />;
  }

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h2 className="text-2xl font-bold text-slate-900 dark:text-white tracking-tight">
          System Rules & Configuration
        </h2>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
          Define working shift policies, grace thresholds, weekly off days, and verify Gmail SMTP delivery
        </p>
      </div>

      {/* Email / SMTP Configuration & Test Card */}
      <Card
        title="Email / SMTP Delivery Settings"
        subtitle="Gmail SMTP server status used for password resets, email verification, and alerts"
      >
        <div className="space-y-4 pt-2">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
              <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">SMTP Host</span>
              <p className="text-sm font-mono font-bold text-slate-900 dark:text-white mt-1">
                {smtpStatus?.smtp_host || 'smtp.gmail.com'}
              </p>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
              <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">SMTP Port</span>
              <p className="text-sm font-mono font-bold text-slate-900 dark:text-white mt-1">
                {smtpStatus?.smtp_port || 587} (STARTTLS)
              </p>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
              <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">SMTP Username</span>
              <p className="text-sm font-mono font-bold text-slate-900 dark:text-white mt-1 truncate">
                {smtpStatus?.smtp_username || 'attendancesystem55@gmail.com'}
              </p>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 p-4 rounded-xl bg-blue-50/50 dark:bg-blue-950/20 border border-blue-100 dark:border-blue-900/50">
            <div className="flex-1 max-w-sm">
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                Send Verification Test Email To:
              </label>
              <input
                type="email"
                value={testEmailTarget}
                onChange={(e) => setTestEmailTarget(e.target.value)}
                className="w-full bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <Button
              type="button"
              variant="primary"
              size="md"
              loading={testingEmail}
              onClick={handleSendTestEmail}
              icon={Send}
            >
              Send Test Email
            </Button>
          </div>
        </div>
      </Card>

      <form onSubmit={handleSave} className="space-y-6">
        {/* Working Hours & Shift Rules */}
        <Card
          title="Shift Timings & Duration Rules"
          subtitle="Standard office working hours used for calculating attendance, overtime, and tardiness"
        >
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-5 pt-2">
            <Input
              label="Standard Shift Check-In"
              type="time"
              required
              value={settings['shift_start_time'] || '09:00'}
              onChange={(e) => handleChange('shift_start_time', e.target.value)}
            />

            <Input
              label="Standard Shift Check-Out"
              type="time"
              required
              value={settings['shift_end_time'] || '18:00'}
              onChange={(e) => handleChange('shift_end_time', e.target.value)}
            />

            <Input
              label="Default Required Hours / Day"
              type="number"
              step="0.5"
              required
              value={settings['default_working_hours'] || '8.0'}
              onChange={(e) => handleChange('default_working_hours', e.target.value)}
              helperText="Hours required for a full PRESENT status"
            />

            <Input
              label="Grace Period (Minutes)"
              type="number"
              required
              value={settings['grace_period_minutes'] || '15'}
              onChange={(e) => handleChange('grace_period_minutes', e.target.value)}
              helperText="Late check-in tolerance before marking tardiness"
            />

            <Input
              label="Half Day Threshold (Hours)"
              type="number"
              step="0.5"
              required
              value={settings['half_day_hours'] || '4.0'}
              onChange={(e) => handleChange('half_day_hours', e.target.value)}
              helperText="Minimum hours to qualify for half-day credit"
            />

            <Input
              label="Overtime Trigger Threshold (Hours)"
              type="number"
              step="0.5"
              required
              value={settings['overtime_threshold_hours'] || '8.0'}
              onChange={(e) => handleChange('overtime_threshold_hours', e.target.value)}
              helperText="Hours beyond which overtime compensation applies"
            />
          </div>
        </Card>

        {/* Weekly Off Days Policy */}
        <Card
          title="Weekly Off Days"
          subtitle="Days marked automatically as WEEK_OFF during daily attendance initialization"
        >
          <div className="pt-2">
            <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-7 gap-2.5">
              {daysOfWeek.map((day) => {
                const isOff = isWeeklyOff(day);
                return (
                  <button
                    key={day}
                    type="button"
                    onClick={() => toggleWeeklyOff(day)}
                    className={`p-3 rounded-xl border text-center transition-all flex flex-col items-center justify-center gap-1 ${
                      isOff
                        ? 'bg-blue-50 border-blue-300 text-blue-700 dark:bg-blue-950/60 dark:border-blue-700 dark:text-blue-300 font-bold'
                        : 'bg-slate-50/70 border-slate-200 text-slate-600 dark:bg-slate-800/40 dark:border-slate-700 dark:text-slate-400 font-medium'
                    }`}
                  >
                    <span className="text-xs">{day.slice(0, 3)}</span>
                    <span className="text-[10px] uppercase">{isOff ? 'Off' : 'Work'}</span>
                  </button>
                );
              })}
            </div>
            <p className="text-xs text-slate-400 mt-3">
              Selected days: <strong className="text-slate-700 dark:text-slate-300">{settings['weekly_off_days'] || 'None'}</strong>
            </p>
          </div>
        </Card>

        {/* General Company Information */}
        <Card
          title="Organization Information"
          subtitle="Company name and notification headers displayed on statements"
        >
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-5 pt-2">
            <Input
              label="Company Name"
              value={settings['company_name'] || 'WorkforceHub Enterprise'}
              onChange={(e) => handleChange('company_name', e.target.value)}
            />

            <Input
              label="Notification Email"
              type="email"
              value={settings['admin_notification_email'] || 'attendancesystem55@gmail.com'}
              onChange={(e) => handleChange('admin_notification_email', e.target.value)}
            />
          </div>
        </Card>

        <div className="flex items-center justify-end gap-3 pt-4">
          <Button
            type="submit"
            variant="primary"
            size="lg"
            loading={saving}
            icon={Save}
          >
            Save All Configurations
          </Button>
        </div>
      </form>
    </div>
  );
};
