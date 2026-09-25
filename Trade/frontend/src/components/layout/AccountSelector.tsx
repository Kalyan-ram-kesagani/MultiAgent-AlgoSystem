import { useState, useEffect, useRef } from 'react';
import { useAccount } from '@/hooks/useAccount';
import { StatusDot } from '@/components/ui/StatusDot';
import { ChevronDown, Plus, Layers } from 'lucide-react';
import { cn } from '@/utils/format';

export function AccountSelector() {
  const { accounts, selectedAccount, selectedAccountId, selectAccount, isAllAccounts } = useAccount();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  const displayName = isAllAccounts
    ? 'All Accounts'
    : selectedAccount?.accountName ?? 'Select Account';

  const displaySub = isAllAccounts
    ? `${accounts.length} accounts`
    : selectedAccount
    ? `MT5 ${selectedAccount.maskedNumber}`
    : '';

  const displayStatus = isAllAccounts
    ? accounts.some((a) => a.status === 'connected')
      ? 'online'
      : 'offline'
    : selectedAccount?.status === 'connected'
    ? 'online'
    : 'offline';

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen(!open)}
        className={cn(
          'flex items-center gap-3 px-3 py-2 rounded-lg border border-border',
          'hover:border-text-muted transition-colors',
          'bg-surface-raised text-left min-w-[220px]'
        )}
      >
        <StatusDot status={displayStatus} size="sm" />
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-text-primary truncate">{displayName}</p>
          <p className="text-[11px] text-text-muted truncate">{displaySub}</p>
        </div>
        <ChevronDown
          size={14}
          className={cn(
            'text-text-muted transition-transform duration-200',
            open && 'rotate-180'
          )}
        />
      </button>

      {open && (
        <div className="absolute top-full left-0 mt-1 w-72 bg-surface-raised border border-border rounded-lg shadow-xl z-50 animate-fade-in overflow-hidden">
          <div className="px-3 py-2 border-b border-border">
            <p className="text-[10px] font-semibold uppercase tracking-wider text-text-muted">
              Select Account
            </p>
          </div>

          {/* All Accounts */}
          <button
            onClick={() => {
              selectAccount(null);
              setOpen(false);
            }}
            className={cn(
              'w-full flex items-center gap-3 px-3 py-2.5 hover:bg-surface-overlay transition-colors text-left',
              isAllAccounts && 'bg-surface-overlay'
            )}
          >
            <Layers size={14} className="text-accent" />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-text-primary">All Accounts</p>
              <p className="text-[11px] text-text-muted">
                Aggregated view · {accounts.length} accounts
              </p>
            </div>
          </button>

          <div className="border-t border-border" />

          {/* Individual Accounts */}
          {accounts.map((account) => (
            <button
              key={account.id}
              onClick={() => {
                selectAccount(account.id);
                setOpen(false);
              }}
              className={cn(
                'w-full flex items-center gap-3 px-3 py-2.5 hover:bg-surface-overlay transition-colors text-left',
                selectedAccountId === account.id && 'bg-surface-overlay'
              )}
            >
              <StatusDot
                status={account.status === 'connected' ? 'online' : 'offline'}
                size="sm"
              />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-text-primary">{account.accountName}</p>
                <p className="text-[11px] text-text-muted">
                  MT5 {account.maskedNumber} · {account.broker}
                </p>
              </div>
              {selectedAccountId === account.id && (
                <div className="w-1.5 h-1.5 rounded-full bg-accent" />
              )}
            </button>
          ))}

          <div className="border-t border-border">
            <button className="w-full flex items-center gap-2 px-3 py-2.5 text-accent text-sm hover:bg-surface-overlay transition-colors">
              <Plus size={14} />
              Add MT5 Account
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
