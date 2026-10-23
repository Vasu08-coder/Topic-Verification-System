import React from 'react';

export default function Card({ children, className = '', title, subtitle, footer }) {
  return (
    <div className={`bg-[#FAF8F5] border border-[#E6E2D6] rounded-xl shadow-xs overflow-hidden ${className}`}>
      {(title || subtitle) && (
        <div className="px-6 py-4 border-b border-[#E6E2D6] bg-[#F5F3ED]/50">
          {title && <h3 className="font-['Source_Serif_4',serif] text-xl font-semibold text-[#182B4D]">{title}</h3>}
          {subtitle && <p className="text-xs text-slate-600 mt-0.5">{subtitle}</p>}
        </div>
      )}
      <div className="p-6">{children}</div>
      {footer && <div className="px-6 py-3.5 bg-[#F5F3ED]/40 border-t border-[#E6E2D6]">{footer}</div>}
    </div>
  );
}