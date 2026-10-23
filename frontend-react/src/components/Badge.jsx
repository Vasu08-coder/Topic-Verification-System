import React from 'react';

export default function Badge({ children, variant = 'neutral', className = '' }) {
  const variants = {
    neutral: 'bg-slate-200 text-slate-800 border-slate-300',
    success: 'bg-emerald-50 text-emerald-800 border-emerald-200',
    warning: 'bg-amber-50 text-amber-800 border-amber-200',
    danger: 'bg-rose-50 text-rose-800 border-rose-200',
    gold: 'bg-[#9C7A32]/10 text-[#9C7A32] border-[#9C7A32]/30',
  };

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border ${variants[variant] || variants.neutral} ${className}`}
    >
      {children}
    </span>
  );
}