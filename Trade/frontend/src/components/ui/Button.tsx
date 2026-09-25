import { cn } from '@/utils/format';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  icon?: React.ReactNode;
}

const variantClasses = {
  primary:
    'bg-accent text-white hover:bg-accent-hover active:scale-[0.98] disabled:opacity-50',
  secondary:
    'bg-surface-overlay text-text-primary border border-border hover:border-text-muted active:scale-[0.98] disabled:opacity-50',
  ghost:
    'text-text-secondary hover:text-text-primary hover:bg-surface-overlay active:scale-[0.98]',
  danger:
    'bg-loss/10 text-loss hover:bg-loss/20 active:scale-[0.98] disabled:opacity-50',
};

const sizeClasses = {
  sm: 'px-3 py-1.5 text-xs',
  md: 'px-4 py-2 text-sm',
  lg: 'px-5 py-2.5 text-sm',
};

export function Button({
  variant = 'primary',
  size = 'md',
  loading,
  icon,
  children,
  className,
  disabled,
  ...props
}: ButtonProps) {
  return (
    <button
      className={cn(
        'inline-flex items-center justify-center gap-2 rounded-lg font-medium transition-all duration-150',
        variantClasses[variant],
        sizeClasses[size],
        className
      )}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? (
        <span className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
      ) : (
        icon
      )}
      {children}
    </button>
  );
}
