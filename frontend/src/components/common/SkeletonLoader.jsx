import React from 'react';

export const SkeletonLoader = ({
  rows = 5,
  type = 'table',
  className = '',
}) => {
  if (type === 'card') {
    return (
      <div className={`grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 ${className}`}>
        {Array.from({ length: rows }).map((_, i) => (
          <div key={i} className="p-6 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 animate-pulse">
            <div className="flex items-center justify-between mb-4">
              <div className="w-10 h-10 bg-slate-200 dark:bg-slate-800 rounded-xl" />
              <div className="w-12 h-5 bg-slate-200 dark:bg-slate-800 rounded-full" />
            </div>
            <div className="h-4 bg-slate-200 dark:bg-slate-800 rounded w-1/2 mb-2" />
            <div className="h-7 bg-slate-200 dark:bg-slate-800 rounded w-3/4" />
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className={`w-full space-y-3 animate-pulse p-4 ${className}`}>
      <div className="h-8 bg-slate-200 dark:bg-slate-800 rounded-lg w-full" />
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex gap-4 items-center">
          <div className="h-10 bg-slate-100 dark:bg-slate-800/60 rounded-lg flex-1" />
          <div className="h-10 bg-slate-100 dark:bg-slate-800/60 rounded-lg flex-1" />
          <div className="h-10 bg-slate-100 dark:bg-slate-800/60 rounded-lg w-24" />
        </div>
      ))}
    </div>
  );
};
