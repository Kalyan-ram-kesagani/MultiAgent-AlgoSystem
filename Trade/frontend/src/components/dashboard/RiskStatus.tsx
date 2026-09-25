import type { RiskStatus as RiskStatusType } from '@/types';
import { Shield, AlertTriangle, Lock } from 'lucide-react';

interface RiskStatusProps {
  risk: RiskStatusType;
}

export function RiskStatusCard({ risk }: RiskStatusProps) {
  const percentage = (risk.dailyRisk / risk.dailyLimit) * 100;

  return (
    <div className="card">
      <h3 className="text-sm font-medium text-text-primary mb-3">Risk Status</h3>

      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-xs text-text-secondary">Daily Risk</span>
          <span className="text-sm font-semibold text-text-primary">{risk.dailyRisk.toFixed(1)}%</span>
        </div>

        <div className="flex items-center justify-between">
          <span className="text-xs text-text-secondary">Daily Limit</span>
          <span className="text-sm font-semibold text-text-primary">{risk.dailyLimit.toFixed(1)}%</span>
        </div>

        {/* Progress bar */}
        <div className="h-1.5 bg-surface-overlay rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-500 ${
              risk.status === 'within_limit'
                ? 'bg-profit'
                : risk.status === 'approaching'
                ? 'bg-warning'
                : 'bg-loss'
            }`}
            style={{ width: `${Math.min(percentage, 100)}%` }}
          />
        </div>

        <div className="flex items-center gap-2 pt-1">
          {risk.status === 'within_limit' && (
            <>
              <Shield size={13} className="text-profit" />
              <span className="text-xs font-medium text-profit">Within Limit</span>
            </>
          )}
          {risk.status === 'approaching' && (
            <>
              <AlertTriangle size={13} className="text-warning" />
              <span className="text-xs font-medium text-warning">Risk Limit Approaching</span>
            </>
          )}
          {risk.status === 'locked' && (
            <>
              <Lock size={13} className="text-loss" />
              <span className="text-xs font-medium text-loss">Trading Locked</span>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
