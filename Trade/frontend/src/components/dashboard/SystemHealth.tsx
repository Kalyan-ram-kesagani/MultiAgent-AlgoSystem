import type { SystemHealthItem } from '@/types';
import { StatusDot } from '@/components/ui/StatusDot';
import { Sparkles } from 'lucide-react';

interface SystemHealthProps {
  items: SystemHealthItem[];
}

export function SystemHealth({ items }: SystemHealthProps) {
  return (
    <div className="card">
      <h3 className="text-sm font-medium text-text-primary mb-3">System Health</h3>
      <div className="space-y-2">
        {items.map((item) => (
          <div key={item.name} className="flex items-center justify-between py-1">
            <span className="text-xs text-text-secondary">{item.name}</span>
            {item.status === 'coming_soon' ? (
              <span className="flex items-center gap-1.5 text-[10px] font-medium text-text-muted">
                <Sparkles size={10} />
                Coming Soon
              </span>
            ) : (
              <div className="flex items-center gap-1.5">
                <StatusDot
                  status={
                    item.status === 'ok'
                      ? 'online'
                      : item.status === 'warning'
                      ? 'warning'
                      : 'offline'
                  }
                  size="sm"
                />
                <span
                  className={`text-[11px] font-medium ${
                    item.status === 'ok'
                      ? 'text-profit'
                      : item.status === 'warning'
                      ? 'text-warning'
                      : 'text-loss'
                  }`}
                >
                  {item.status === 'ok' ? 'OK' : item.status === 'warning' ? 'Warning' : 'Error'}
                </span>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
