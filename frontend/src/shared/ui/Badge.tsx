import React from 'react';
import { cn } from '../lib/utils';

export type BadgeVariant = 'sano' | 'antracnosis' | 'plaga' | 'deficiencia' | 'neutral';

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant;
  children: React.ReactNode;
}

const variantStyles: Record<BadgeVariant, string> = {
  sano: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
  antracnosis: 'bg-rose-500/15 text-rose-400 border-rose-500/30',
  plaga: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
  deficiencia: 'bg-violet-500/15 text-violet-400 border-violet-500/30',
  neutral: 'bg-slate-800 text-slate-300 border-slate-700',
};

export const Badge: React.FC<BadgeProps> = ({
  variant = 'neutral',
  className,
  children,
  ...props
}) => {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold border tracking-wide uppercase',
        variantStyles[variant],
        className,
      )}
      {...props}
    >
      <span className="w-1.5 h-1.5 rounded-full bg-current opacity-80 animate-pulse" />
      {children}
    </span>
  );
};
