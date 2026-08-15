import React from 'react';

export const Table = ({
  headers = [],
  children,
  className = '',
}) => {
  return (
    <div className="w-full overflow-x-auto">
      <table className={`w-full text-left border-collapse ${className}`}>
        <thead>
          <tr className="border-b border-slate-200 dark:border-slate-800 bg-slate-50/80 dark:bg-slate-900/60 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
            {headers.map((h, idx) => (
              <th
                key={idx}
                className={`py-3.5 px-4 first:pl-6 last:pr-6 whitespace-nowrap ${
                  h.align === 'right'
                    ? 'text-right'
                    : h.align === 'center'
                    ? 'text-center'
                    : 'text-left'
                } ${h.className || ''}`}
              >
                {typeof h === 'string' ? h : h.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100 dark:divide-slate-800/80 text-sm text-slate-700 dark:text-slate-200">
          {children}
        </tbody>
      </table>
    </div>
  );
};
