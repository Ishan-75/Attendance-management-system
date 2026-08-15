import React from 'react';
import { Link } from 'react-router-dom';
import { Menu, Sun, Moon, LogOut, RefreshCw, Wifi, WifiOff, AlertTriangle, CheckCircle2 } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useTheme } from '../../context/ThemeContext';
import { useSync } from '../../context/SyncContext';

export const Topbar = ({ onOpenSidebar }) => {
  const { user, logout, isAdmin } = useAuth();
  const { theme, toggleTheme, isDark } = useTheme();
  const { isOnline, isSyncing, pendingCount, conflictsCount, syncNow } = useSync();

  return (
    <header className="h-16 sticky top-0 z-30 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md border-b border-slate-200/80 dark:border-slate-800 flex items-center justify-between px-4 sm:px-6 lg:px-8 transition-colors">
      {/* Left side: Hamburger button + role badge */}
      <div className="flex items-center gap-4">
        <button
          type="button"
          onClick={onOpenSidebar}
          className="lg:hidden p-2 rounded-xl text-slate-500 hover:text-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 dark:hover:text-slate-300 transition-colors"
        >
          <Menu className="w-5 h-5" />
        </button>

        <div className="hidden sm:flex items-center gap-2">
          <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-slate-100 text-slate-700 border border-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-700">
            {isAdmin ? 'Admin Console' : 'Manager Portal'}
          </span>
        </div>
      </div>

      {/* Right side: Sync Status, Theme Toggle, Profile */}
      <div className="flex items-center gap-3">
        {/* Offline / Online Sync Indicator Badge */}
        <div className="flex items-center gap-2">
          {isOnline ? (
            <div className="flex items-center gap-2 bg-emerald-50 text-emerald-700 border border-emerald-200 dark:bg-emerald-950/60 dark:text-emerald-300 dark:border-emerald-800 px-2.5 py-1 rounded-full text-xs font-semibold">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span className="hidden md:inline">Online</span>
            </div>
          ) : (
            <div className="flex items-center gap-2 bg-rose-50 text-rose-700 border border-rose-200 dark:bg-rose-950/60 dark:text-rose-300 dark:border-rose-800 px-2.5 py-1 rounded-full text-xs font-semibold">
              <span className="w-2 h-2 rounded-full bg-rose-500" />
              <span>Offline ({pendingCount} pending)</span>
            </div>
          )}

          {/* Pending Changes / Sync Now Button */}
          <button
            onClick={() => syncNow(false)}
            disabled={isSyncing || !isOnline}
            title="Synchronize local changes with central MySQL database"
            className="flex items-center gap-1.5 px-3 py-1 text-xs font-semibold rounded-full bg-blue-50 text-blue-700 hover:bg-blue-100 border border-blue-200 dark:bg-blue-950/60 dark:text-blue-300 dark:border-blue-800 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isSyncing ? 'animate-spin' : ''}`} />
            <span className="hidden sm:inline">{isSyncing ? 'Syncing...' : 'Sync Now'}</span>
          </button>

          {/* Conflict Alert Link if any */}
          {conflictsCount > 0 && (
            <Link
              to="/sync-conflicts"
              className="flex items-center gap-1.5 px-2.5 py-1 text-xs font-bold rounded-full bg-amber-50 text-amber-700 border border-amber-300 dark:bg-amber-950/80 dark:text-amber-300 dark:border-amber-700 animate-bounce"
            >
              <AlertTriangle className="w-3.5 h-3.5" />
              <span>{conflictsCount} Conflict{conflictsCount > 1 ? 's' : ''}</span>
            </Link>
          )}
        </div>

        {/* Dark/Light mode toggle */}
        <button
          onClick={toggleTheme}
          title={isDark ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
          className="p-2 rounded-xl text-slate-500 hover:text-slate-800 hover:bg-slate-100 dark:hover:bg-slate-800 dark:hover:text-slate-200 transition-colors"
        >
          {isDark ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-slate-600" />}
        </button>

        {/* User Pill */}
        <div className="flex items-center gap-3 pl-2 border-l border-slate-200 dark:border-slate-800">
          <div className="flex flex-col items-end">
            <span className="text-xs font-semibold text-slate-800 dark:text-slate-200">
              {user?.full_name || user?.username || 'Rajavel'}
            </span>
            <span className="text-[10px] text-slate-400 dark:text-slate-500">
              {user?.email}
            </span>
          </div>

          <div className="w-8 h-8 rounded-full bg-blue-600/10 text-blue-600 dark:bg-blue-500/20 dark:text-blue-400 flex items-center justify-center font-bold text-xs">
            {user?.full_name ? user.full_name.charAt(0).toUpperCase() : (user?.username ? user.username.charAt(0).toUpperCase() : 'R')}
          </div>
        </div>
      </div>
    </header>
  );
};
