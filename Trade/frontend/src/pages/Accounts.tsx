import { useAccount } from '@/hooks/useAccount';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { StatusDot } from '@/components/ui/StatusDot';
import { formatCurrency, formatRelativeTime } from '@/utils/format';
import { Plus, Wifi, WifiOff, Trash2, RefreshCw, Clock } from 'lucide-react';

export default function Accounts() {
  const { accounts } = useAccount();

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold text-text-primary">Accounts</h1>
          <p className="text-sm text-text-secondary mt-0.5">
            Manage your MT5 trading accounts
          </p>
        </div>
        <Button icon={<Plus size={14} />}>Add MT5 Account</Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {accounts.map((account) => {
          const isConnected = account.status === 'connected';

          return (
            <div key={account.id} className="card">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-lg ${isConnected ? 'bg-profit/10' : 'bg-surface-overlay'}`}>
                    {isConnected ? (
                      <Wifi size={18} className="text-profit" />
                    ) : (
                      <WifiOff size={18} className="text-text-muted" />
                    )}
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-text-primary">{account.accountName}</h3>
                    <p className="text-xs text-text-muted">
                      MT5 {account.maskedNumber} · {account.broker}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant={isConnected ? 'success' : 'neutral'}>
                    {isConnected ? 'Connected' : 'Disconnected'}
                  </Badge>
                  <Badge variant={account.accountType === 'live' ? 'default' : 'warning'}>
                    {account.accountType.toUpperCase()}
                  </Badge>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 mb-4">
                <div>
                  <p className="text-[10px] text-text-muted uppercase tracking-wider">Balance</p>
                  <p className="text-sm font-semibold text-text-primary">
                    {formatCurrency(account.balance).replace('+', '')}
                  </p>
                </div>
                <div>
                  <p className="text-[10px] text-text-muted uppercase tracking-wider">Equity</p>
                  <p className="text-sm font-semibold text-text-primary">
                    {formatCurrency(account.equity).replace('+', '')}
                  </p>
                </div>
                <div>
                  <p className="text-[10px] text-text-muted uppercase tracking-wider">Currency</p>
                  <p className="text-sm font-medium text-text-primary">{account.currency}</p>
                </div>
                <div>
                  <p className="text-[10px] text-text-muted uppercase tracking-wider">Last Sync</p>
                  <p className="text-sm text-text-secondary flex items-center gap-1">
                    <Clock size={11} />
                    {account.lastSync ? formatRelativeTime(account.lastSync) : 'Never'}
                  </p>
                </div>
              </div>

              <div className="flex items-center justify-between pt-3 border-t border-border">
                <div className="flex items-center gap-1.5">
                  <StatusDot status={isConnected ? 'online' : 'offline'} size="sm" />
                  <span className="text-xs text-text-muted">
                    {isConnected ? 'Live connection' : 'No connection'}
                  </span>
                </div>
                <div className="flex items-center gap-1.5">
                  <Button variant="ghost" size="sm" icon={<RefreshCw size={12} />}>
                    Sync
                  </Button>
                  <Button variant="danger" size="sm" icon={<Trash2 size={12} />}>
                    Remove
                  </Button>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
