import { cn } from '@/utils/format';

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'default' | 'success' | 'danger' | 'warning' | 'neutral';
  size?: 'sm' | 'md';
}

const variantClasses = {
  default: 'bg-accent/10 text-accent',
  success: 'bg-profit-subtle text-profit',
  danger: 'bg-loss-subtle text-loss',
  warning: 'bg-warning-subtle text-warning',
  neutral: 'bg-surface-overlay text-text-secondary',
};

export function Badge({ children, variant = 'default', size = 'sm' }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center font-medium rounded-full',
        variantClasses[variant],
        size === 'sm' ? 'px-2 py-0.5 text-[10px]' : 'px-2.5 py-1 text-xs'
      )}
    >
      {children}
    </span>
  );
}
