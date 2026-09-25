import { cn } from '@/utils/format';

interface StatusDotProps {
  status: 'online' | 'offline' | 'warning';
  size?: 'sm' | 'md';
}

export function StatusDot({ status, size = 'md' }: StatusDotProps) {
  return (
    <span
      className={cn(
        'status-dot',
        status === 'online' && 'status-dot--online',
        status === 'offline' && 'status-dot--offline',
        status === 'warning' && 'status-dot--warning',
        size === 'sm' && '!w-[6px] !h-[6px]'
      )}
    />
  );
}
