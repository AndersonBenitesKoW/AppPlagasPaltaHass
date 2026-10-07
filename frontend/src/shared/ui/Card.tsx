import React from 'react';
import { cn } from '../lib/utils';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  hoverEffect?: boolean;
}

export const Card: React.FC<CardProps> = ({
  hoverEffect = true,
  className,
  children,
  ...props
}) => {
  return (
    <div
      className={cn(
        'glass-panel rounded-2xl p-6 transition-all duration-300',
        hoverEffect && 'glass-panel-hover hover:-translate-y-0.5',
        className,
      )}
      {...props}
    >
      {children}
    </div>
  );
};
