import { cn } from '@/utils/format';

interface MetricCardProps {
  label: string;
  value: string;
  valueClass?: string;
  subtitle?: string;
  icon?: React.ReactNode;
}

export function MetricCard({ label, value, valueClass, subtitle, icon }: MetricCardProps) {
  return (
    <div className="card group">
      <div className="flex items-start justify-between">
        <div className="space-y-1.5">
          <p className="text-xs font-medium uppercase tracking-wider text-text-muted">
            {label}
          </p>
          <p className={cn('text-2xl font-semibold tracking-tight', valueClass)}>
            {value}
          </p>
          {subtitle && (
            <p className="text-xs text-text-muted">{subtitle}</p>
          )}
        </div>
        {icon && (
          <div className="text-text-muted opacity-60 group-hover:opacity-100 transition-opacity">
            {icon}
          </div>
        )}
      </div>
    </div>
  );
}
