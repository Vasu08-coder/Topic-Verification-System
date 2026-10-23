import React from 'react';

export default function Button({
  children,
  variant = 'primary',
  type = 'button',
  onClick,
  disabled = false,
  className = '',
}) {
  const baseStyles = 'inline-flex items-center justify-center px-4 py-2.5 rounded-lg text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed';
  
  const variants = {
    primary: 'bg-[#182B4D] text-[#F5F3ED] hover:bg-[#101B33] focus:ring-[#182B4D]',
    accent: 'bg-[#9C7A32] text-white hover:bg-[#856729] focus:ring-[#9C7A32]',
    outline: 'border border-[#182B4D]/30 text-[#182B4D] hover:bg-[#182B4D]/5 focus:ring-[#182B4D]',
    danger: 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500',
  };

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={`${baseStyles} ${variants[variant] || variants.primary} ${className}`}
    >
      {children}
    </button>
  );
}