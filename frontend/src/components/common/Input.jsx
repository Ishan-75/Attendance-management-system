import React, { forwardRef } from 'react';

export const Input = forwardRef(({
  label,
  error,
  helperText,
  icon: Icon,
  className = '',
  id,
  required = false,
  ...props
}, ref) => {
  const inputId = id || (label ? label.toLowerCase().replace(/\s+/g, '-') : undefined);

  return (
    <div className="w-full">
      {label && (
        <label htmlFor={inputId} className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">
          {label}
          {required && <span className="text-rose-500 ml-1">*</span>}
        </label>
      )}
      <div className="relative rounded-lg shadow-sm">
        {Icon && (
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400 dark:text-slate-500">
            <Icon className="w-4 h-4" />
          </div>
        )}
        <input
          ref={ref}
          id={inputId}
          className={`block w-full rounded-lg text-sm bg-white dark:bg-slate-900 border transition-all duration-150
            ${Icon ? 'pl-9' : 'pl-3.5'} pr-3.5 py-2
            ${
              error
                ? 'border-rose-300 text-rose-900 placeholder-rose-400 focus:outline-none focus:ring-2 focus:ring-rose-500 focus:border-rose-500 dark:border-rose-600 dark:text-rose-100'
                : 'border-slate-300 dark:border-slate-700 text-slate-900 dark:text-slate-100 placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }
            disabled:bg-slate-50 disabled:text-slate-500 disabled:border-slate-200 dark:disabled:bg-slate-800 dark:disabled:text-slate-500
            ${className}`}
          {...props}
        />
      </div>
      {error && <p className="mt-1 text-xs text-rose-600 dark:text-rose-400">{error}</p>}
      {!error && helperText && <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">{helperText}</p>}
    </div>
  );
});

Input.displayName = 'Input';
