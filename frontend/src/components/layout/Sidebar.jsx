import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  CalendarCheck,
  Users,
  CalendarDays,
  Building2,
  FileSpreadsheet,
  History,
  Database,
  Settings,
  Sparkles,
  ChevronRight,
  SunMedium,
  LogOut,
  UserCheck,
  Smartphone,
  AlertTriangle
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export const Sidebar = ({ isOpen, onClose }) => {
  const { user, isAdmin, logout } = useAuth();
  const location = useLocation();

  const navSections = [
    {
      title: 'Workforce',
      items: [
        { name: 'Dashboard', path: '/', icon: LayoutDashboard },
        { name: 'Attendance Sheet', path: '/attendance', icon: CalendarCheck },
        { name: 'Employees', path: '/employees', icon: Users },
        { name: 'Leave Requests', path: '/leaves', icon: CalendarDays },
      ],
    },
    {
      title: 'Analytics & Management',
      items: [
        { name: 'Reports & Export', path: '/reports', icon: FileSpreadsheet },
        { name: 'Departments', path: '/departments', icon: Building2 },
        { name: 'Company Holidays', path: '/holidays', icon: SunMedium },
        { name: 'Sync Conflicts', path: '/sync-conflicts', icon: AlertTriangle },
      ],
    },
  ];

  if (isAdmin) {
    navSections.push({
      title: 'Administration',
      items: [
        { name: 'Registered Devices', path: '/devices', icon: Smartphone },
        { name: 'User Accounts', path: '/users', icon: UserCheck },
        { name: 'Audit Logs', path: '/audit-logs', icon: History },
        { name: 'Backup & Restore', path: '/backup-restore', icon: Database },
        { name: 'System Settings', path: '/settings', icon: Settings },
      ],
    });
  }

  return (
    <>
      {/* Mobile backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-slate-950/60 backdrop-blur-sm lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={`fixed top-0 bottom-0 left-0 z-40 w-64 bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800/90 flex flex-col transition-transform duration-300 ease-in-out lg:translate-x-0 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Brand Header */}
        <div className="h-16 flex items-center gap-3 px-6 border-b border-slate-100 dark:border-slate-800">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center text-white shadow-md shadow-blue-500/20">
            <CalendarCheck className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-sm font-bold text-slate-900 dark:text-white tracking-tight leading-none">
              WorkforceHub
            </h1>
            <span className="text-[11px] font-medium text-slate-400 dark:text-slate-500">
              Attendance Suite
            </span>
          </div>
        </div>

        {/* Navigation items */}
        <div className="flex-1 overflow-y-auto px-4 py-5 space-y-6">
          {navSections.map((section, idx) => (
            <div key={idx} className="space-y-1">
              <div className="px-3 text-[11px] font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500 mb-2">
                {section.title}
              </div>
              {section.items.map((item) => {
                const Icon = item.icon;
                const isActive = location.pathname === item.path;

                return (
                  <NavLink
                    key={item.path}
                    to={item.path}
                    onClick={() => {
                      if (window.innerWidth < 1024) onClose();
                    }}
                    className={`flex items-center justify-between px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-150 group ${
                      isActive
                        ? 'bg-blue-50 text-blue-700 font-semibold dark:bg-blue-600/10 dark:text-blue-400'
                        : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800/60 hover:text-slate-900 dark:hover:text-slate-200'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <Icon
                        className={`w-4 h-4 transition-colors ${
                          isActive
                            ? 'text-blue-600 dark:text-blue-400'
                            : 'text-slate-400 dark:text-slate-500 group-hover:text-slate-600 dark:group-hover:text-slate-300'
                        }`}
                      />
                      <span>{item.name}</span>
                    </div>
                    {isActive && (
                      <div className="w-1.5 h-1.5 rounded-full bg-blue-600 dark:bg-blue-400" />
                    )}
                  </NavLink>
                );
              })}
            </div>
          ))}
        </div>

        {/* User Card in Sidebar Footer */}
        <div className="p-4 border-t border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/40">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3 overflow-hidden">
              <div className="w-9 h-9 rounded-full bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-200 flex items-center justify-center font-bold text-xs shrink-0">
                {user?.full_name ? user.full_name.charAt(0).toUpperCase() : (user?.username ? user.username.charAt(0).toUpperCase() : 'U')}
              </div>
              <div className="overflow-hidden">
                <div className="text-xs font-semibold text-slate-800 dark:text-slate-200 truncate">
                  {user?.full_name || user?.username || 'User'}
                </div>
                <div className="text-[10px] font-medium text-slate-400 dark:text-slate-500 uppercase tracking-wider">
                  {user?.role || 'Manager'}
                </div>
              </div>
            </div>
            <button
              onClick={logout}
              title="Logout"
              className="p-1.5 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/40 transition-colors"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </aside>
    </>
  );
};
