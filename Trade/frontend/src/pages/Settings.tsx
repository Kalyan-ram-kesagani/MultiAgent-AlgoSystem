import { useTheme } from '@/hooks/useTheme';
import { Sun, Moon, Monitor } from 'lucide-react';
import { cn } from '@/utils/format';

export default function Settings() {
  const { theme, toggleTheme } = useTheme();

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-xl font-semibold text-text-primary">Settings</h1>
        <p className="text-sm text-text-secondary mt-0.5">
          Configure your trading platform preferences
        </p>
      </div>

      {/* Theme */}
      <div className="card">
        <h3 className="text-sm font-medium text-text-primary mb-4">Appearance</h3>
        <div className="flex gap-3">
          <button
            onClick={() => theme !== 'dark' && toggleTheme()}
            className={cn(
              'flex-1 flex flex-col items-center gap-2 p-4 rounded-lg border transition-all',
              theme === 'dark'
                ? 'border-accent bg-accent/5'
                : 'border-border hover:border-text-muted'
            )}
          >
            <Moon size={20} className={theme === 'dark' ? 'text-accent' : 'text-text-muted'} />
            <span className="text-sm font-medium text-text-primary">Dark</span>
          </button>
          <button
            onClick={() => theme !== 'light' && toggleTheme()}
            className={cn(
              'flex-1 flex flex-col items-center gap-2 p-4 rounded-lg border transition-all',
              theme === 'light'
                ? 'border-accent bg-accent/5'
                : 'border-border hover:border-text-muted'
            )}
          >
            <Sun size={20} className={theme === 'light' ? 'text-accent' : 'text-text-muted'} />
            <span className="text-sm font-medium text-text-primary">Light</span>
          </button>
        </div>
      </div>

      {/* Trading Preferences */}
      <div className="card">
        <h3 className="text-sm font-medium text-text-primary mb-4">Trading Preferences</h3>
        <div className="space-y-4">
          <div className="flex items-center justify-between py-2 border-b border-border/50">
            <div>
              <p className="text-sm text-text-primary">Default Risk Per Trade</p>
              <p className="text-xs text-text-muted">Maximum risk percentage for new trades</p>
            </div>
            <span className="text-sm font-medium text-text-primary">2.0%</span>
          </div>
          <div className="flex items-center justify-between py-2 border-b border-border/50">
            <div>
              <p className="text-sm text-text-primary">Daily Risk Limit</p>
              <p className="text-xs text-text-muted">Maximum daily risk before trading lock</p>
            </div>
            <span className="text-sm font-medium text-text-primary">5.0%</span>
          </div>
          <div className="flex items-center justify-between py-2">
            <div>
              <p className="text-sm text-text-primary">Auto Risk-Free</p>
              <p className="text-xs text-text-muted">Automatically move SL to breakeven at 1R</p>
            </div>
            <span className="text-sm font-medium text-profit">Enabled</span>
          </div>
        </div>
      </div>

      {/* Notifications */}
      <div className="card">
        <h3 className="text-sm font-medium text-text-primary mb-4">Notifications</h3>
        <div className="space-y-4">
          <div className="flex items-center justify-between py-2 border-b border-border/50">
            <div>
              <p className="text-sm text-text-primary">Trade Opened</p>
              <p className="text-xs text-text-muted">Notify when a new trade is opened</p>
            </div>
            <span className="text-sm font-medium text-profit">On</span>
          </div>
          <div className="flex items-center justify-between py-2 border-b border-border/50">
            <div>
              <p className="text-sm text-text-primary">Trade Closed</p>
              <p className="text-xs text-text-muted">Notify when a trade is closed</p>
            </div>
            <span className="text-sm font-medium text-profit">On</span>
          </div>
          <div className="flex items-center justify-between py-2">
            <div>
              <p className="text-sm text-text-primary">Risk Limit Warning</p>
              <p className="text-xs text-text-muted">Notify when approaching daily risk limit</p>
            </div>
            <span className="text-sm font-medium text-profit">On</span>
          </div>
        </div>
      </div>

      {/* Data */}
      <div className="card">
        <h3 className="text-sm font-medium text-text-primary mb-4">Data</h3>
        <p className="text-xs text-text-secondary">
          Database and data management settings will be available when connected to the backend.
        </p>
      </div>
    </div>
  );
}
