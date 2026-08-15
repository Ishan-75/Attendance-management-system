import React, { forwardRef } from 'react';

export const Select = forwardRef(({
  label,
  options = [],
  error,
  helperText,
  className = '',
  id,
  required = false,
  placeholder,
  ...props
}, ref) => {
  const selectId = id || (label ? label.toLowerCase().replace(/\s+/g, '-') : undefined);

  return (
    <div className="w-full">
      {label && (
        <label htmlFor={selectId} className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">
          {label}
          {required && <span className="text-rose-500 ml-1">*</span>}
        </label>
      )}
      <select
        ref={ref}
        id={selectId}
        className={`block w-full rounded-lg text-sm bg-white dark:bg-slate-900 border transition-all duration-150 px-3 py-2
          ${
            error
              ? 'border-rose-300 text-rose-900 focus:ring-2 focus:ring-rose-500 focus:border-rose-500 dark:border-rose-600 dark:text-rose-100'
              : 'border-slate-300 dark:border-slate-700 text-slate-900 dark:text-slate-100 focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
          }
          disabled:bg-slate-50 disabled:text-slate-500 disabled:border-slate-200 dark:disabled:bg-slate-800 dark:disabled:text-slate-500
          ${className}`}
        {...props}
      >
        {placeholder && <option value="">{placeholder}</option>}
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
      {error && <p className="mt-1 text-xs text-rose-600 dark:text-rose-400">{error}</p>}
      {!error && helperText && <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">{helperText}</p>}
    </div>
  );
});

Select.displayName = 'Select';
