import { AccountSelector } from './AccountSelector';
import { useTheme } from '@/hooks/useTheme';
import { useAccount } from '@/hooks/useAccount';
import { Sun, Moon, Menu, Clock } from 'lucide-react';
import { StatusDot } from '@/components/ui/StatusDot';
import { formatRelativeTime } from '@/utils/format';

interface HeaderProps {
  onMenuClick: () => void;
}

export function Header({ onMenuClick }: HeaderProps) {
  const { theme, toggleTheme } = useTheme();
  const { selectedAccount, dataMode } = useAccount();

  return (
    <header className="flex items-center justify-between px-4 lg:px-6 py-3 border-b border-border bg-surface-raised">
      <div className="flex items-center gap-3">
        {/* Mobile menu button */}
        <button
          onClick={onMenuClick}
          className="lg:hidden p-1.5 rounded-lg hover:bg-surface-overlay text-text-muted"
        >
          <Menu size={20} />
        </button>

        <AccountSelector />
      </div>

      <div className="flex items-center gap-3">
        {/* Data Mode */}
        {dataMode === 'demo' && (
          <span className="hidden sm:inline-flex items-center px-2.5 py-1 text-[10px] font-semibold tracking-wider uppercase rounded-full bg-warning/10 text-warning border border-warning/20">
            Demo Mode
          </span>
        )}

        {/* MT5 Status */}
        {selectedAccount && (
          <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-surface-overlay text-xs">
            <StatusDot
              status={selectedAccount.status === 'connected' ? 'online' : 'offline'}
              size="sm"
            />
            <span className="text-text-secondary">
              MT5 {selectedAccount.status === 'connected' ? 'Connected' : 'Disconnected'}
            </span>
            {selectedAccount.lastSync && (
              <span className="flex items-center gap-1 text-text-muted border-l border-border pl-2">
                <Clock size={10} />
                {formatRelativeTime(selectedAccount.lastSync)}
              </span>
            )}
          </div>
        )}

        {/* Theme Toggle */}
        <button
          onClick={toggleTheme}
          className="p-2 rounded-lg hover:bg-surface-overlay text-text-muted hover:text-text-primary transition-colors"
          aria-label="Toggle theme"
        >
          {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
        </button>
      </div>
    </header>
  );
}
