import React from 'react';

export const Card = ({
  children,
  title,
  subtitle,
  action,
  className = '',
  bodyClassName = 'p-6',
  headerClassName = 'px-6 py-4 border-b border-slate-100 dark:border-slate-800/80',
  footer,
}) => {
  return (
    <div className={`bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 rounded-2xl shadow-sm overflow-hidden transition-all duration-200 ${className}`}>
      {(title || action) && (
        <div className={`flex items-center justify-between ${headerClassName}`}>
          <div>
            {title && (
              <h3 className="text-base font-semibold text-slate-900 dark:text-slate-100">
                {title}
              </h3>
            )}
            {subtitle && (
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                {subtitle}
              </p>
            )}
          </div>
          {action && <div>{action}</div>}
        </div>
      )}
      <div className={bodyClassName}>{children}</div>
      {footer && (
        <div className="px-6 py-3 bg-slate-50 dark:bg-slate-900/50 border-t border-slate-100 dark:border-slate-800 text-xs text-slate-500 dark:text-slate-400">
          {footer}
        </div>
      )}
    </div>
  );
};
