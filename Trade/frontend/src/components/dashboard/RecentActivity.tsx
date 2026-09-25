import type { Activity, ActivityType } from '@/types';
import { formatRelativeTime } from '@/utils/format';
import {
  ArrowUpRight,
  ArrowDownRight,
  Shield,
  Edit3,
  Target,
  Wifi,
  WifiOff,
  RefreshCw,
  Users,
  Play,
  Pause,
  AlertTriangle,
  AlertCircle,
} from 'lucide-react';

const activityIcons: Record<ActivityType, React.ReactNode> = {
  trade_opened: <ArrowUpRight size={14} className="text-accent" />,
  trade_closed: <ArrowDownRight size={14} className="text-profit" />,
  risk_free_activated: <Shield size={14} className="text-profit" />,
  sl_modified: <Edit3 size={14} className="text-warning" />,
  tp_modified: <Target size={14} className="text-accent" />,
  mt5_connected: <Wifi size={14} className="text-profit" />,
  mt5_disconnected: <WifiOff size={14} className="text-loss" />,
  mt5_synchronized: <RefreshCw size={14} className="text-accent" />,
  account_switched: <Users size={14} className="text-text-secondary" />,
  strategy_enabled: <Play size={14} className="text-profit" />,
  strategy_disabled: <Pause size={14} className="text-text-muted" />,
  risk_limit_reached: <AlertTriangle size={14} className="text-loss" />,
  system_warning: <AlertCircle size={14} className="text-warning" />,
};

interface RecentActivityProps {
  activities: Activity[];
}

export function RecentActivity({ activities }: RecentActivityProps) {
  return (
    <div className="card">
      <h3 className="text-sm font-medium text-text-primary mb-4">Recent Activity</h3>
      <div className="space-y-0.5">
        {activities.slice(0, 8).map((activity) => (
          <div
            key={activity.id}
            className="flex items-start gap-3 px-2 py-2.5 rounded-lg hover:bg-surface-overlay transition-colors"
          >
            <div className="mt-0.5 p-1.5 rounded-md bg-surface-overlay">
              {activityIcons[activity.type]}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-text-primary">{activity.title}</p>
              <p className="text-xs text-text-secondary truncate">{activity.description}</p>
            </div>
            <span className="text-[11px] text-text-muted whitespace-nowrap flex-shrink-0">
              {formatRelativeTime(activity.timestamp)}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
