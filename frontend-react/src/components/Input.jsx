import React from 'react';

export default function Input({
  label,
  id,
  type = 'text',
  value,
  onChange,
  placeholder,
  error,
  required = false,
  rows,
  className = '',
}) {
  return (
    <div className={`space-y-1.5 ${className}`}>
      {label && (
        <label htmlFor={id} className="block text-xs font-semibold tracking-wide uppercase text-slate-700">
          {label} {required && <span className="text-red-600">*</span>}
        </label>
      )}
      {rows ? (
        <textarea
          id={id}
          value={value}
          onChange={onChange}
          placeholder={placeholder}
          rows={rows}
          required={required}
          className={`w-full rounded-lg border bg-white px-3.5 py-2.5 text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 transition-all ${
            error
              ? 'border-red-500 focus:ring-red-200'
              : 'border-[#E6E2D6] focus:border-[#182B4D] focus:ring-[#182B4D]/20'
          }`}
        />
      ) : (
        <input
          id={id}
          type={type}
          value={value}
          onChange={onChange}
          placeholder={placeholder}
          required={required}
          className={`w-full rounded-lg border bg-white px-3.5 py-2.5 text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 transition-all ${
            error
              ? 'border-red-500 focus:ring-red-200'
              : 'border-[#E6E2D6] focus:border-[#182B4D] focus:ring-[#182B4D]/20'
          }`}
        />
      )}
      {error && <p className="text-xs text-red-600 mt-1">{error}</p>}
    </div>
  );
}