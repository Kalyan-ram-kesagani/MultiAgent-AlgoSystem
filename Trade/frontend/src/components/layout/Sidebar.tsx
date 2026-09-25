import { NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Activity,
  History,
  BarChart3,
  BookOpen,
  Layers,
  Settings,
  Users,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import { StatusDot } from '@/components/ui/StatusDot';
import { useAccount } from '@/hooks/useAccount';
import { cn } from '@/utils/format';

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
  onMobileClose?: () => void;
}

interface NavItem {
  to: string;
  icon: React.ReactNode;
  label: string;
}

const tradingNav: NavItem[] = [
  { to: '/', icon: <LayoutDashboard size={18} />, label: 'Dashboard' },
  { to: '/live', icon: <Activity size={18} />, label: 'Live Trading' },
  { to: '/history', icon: <History size={18} />, label: 'Trade History' },
];

const analyticsNav: NavItem[] = [
  { to: '/analysis', icon: <BarChart3 size={18} />, label: 'Analysis' },
  { to: '/journal', icon: <BookOpen size={18} />, label: 'Journal' },
  { to: '/strategies', icon: <Layers size={18} />, label: 'Strategies' },
];

const systemNav: NavItem[] = [
  { to: '/accounts', icon: <Users size={18} />, label: 'Accounts' },
  { to: '/settings', icon: <Settings size={18} />, label: 'Settings' },
];

function NavSection({ title, items, collapsed, onMobileClose }: { title: string; items: NavItem[]; collapsed: boolean; onMobileClose?: () => void }) {
  const location = useLocation();

  return (
    <div className="mb-6">
      {!collapsed && (
        <p className="px-3 mb-2 text-[10px] font-semibold uppercase tracking-widest text-text-muted">
          {title}
        </p>
      )}
      <nav className="space-y-0.5">
        {items.map((item) => {
          const isActive =
            item.to === '/' ? location.pathname === '/' : location.pathname.startsWith(item.to);

          return (
            <NavLink
              key={item.to}
              to={item.to}
              onClick={onMobileClose}
              className={cn(
                'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-150',
                isActive
                  ? 'bg-accent/10 text-accent'
                  : 'text-text-secondary hover:text-text-primary hover:bg-surface-overlay'
              )}
              title={collapsed ? item.label : undefined}
            >
              <span className="flex-shrink-0">{item.icon}</span>
              {!collapsed && <span>{item.label}</span>}
            </NavLink>
          );
        })}
      </nav>
    </div>
  );
}

export function Sidebar({ collapsed, onToggle, onMobileClose }: SidebarProps) {
  const { selectedAccount, dataMode } = useAccount();
  const isConnected = selectedAccount?.status === 'connected';

  return (
    <aside
      className={cn(
        'flex flex-col h-full bg-surface-raised border-r border-border transition-all duration-200',
        collapsed ? 'w-[60px]' : 'w-[220px]'
      )}
    >
      {/* Logo / Title */}
      <div className="flex items-center justify-between px-3 py-4 border-b border-border">
        {!collapsed && (
          <div>
            <h1 className="text-sm font-bold text-text-primary tracking-tight">
              Trading System
            </h1>
          </div>
        )}
        <button
          onClick={onToggle}
          className="p-1 rounded hover:bg-surface-overlay text-text-muted hover:text-text-primary transition-colors"
          aria-label="Toggle sidebar"
        >
          {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
        </button>
      </div>

      {/* Navigation */}
      <div className="flex-1 overflow-y-auto px-2 py-4">
        <NavSection title="Trading System" items={tradingNav} collapsed={collapsed} onMobileClose={onMobileClose} />
        <NavSection title="Analytics" items={analyticsNav} collapsed={collapsed} onMobileClose={onMobileClose} />
        <NavSection title="System" items={systemNav} collapsed={collapsed} onMobileClose={onMobileClose} />
      </div>

      {/* Footer Status */}
      <div className="px-3 py-3 border-t border-border space-y-2">
        {!collapsed ? (
          <>
            <div className="flex items-center gap-2">
              <StatusDot status={isConnected ? 'online' : 'offline'} size="sm" />
              <span className="text-xs text-text-secondary">
                System {isConnected ? 'Online' : 'Offline'}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <StatusDot status={isConnected ? 'online' : 'offline'} size="sm" />
              <span className="text-xs text-text-secondary">
                MT5 {isConnected ? 'Connected' : 'Disconnected'}
              </span>
            </div>
            {dataMode === 'demo' && (
              <div className="mt-1">
                <span className="inline-flex items-center px-2 py-0.5 text-[10px] font-semibold tracking-wider uppercase rounded bg-warning/10 text-warning">
                  Demo Mode
                </span>
              </div>
            )}
          </>
        ) : (
          <div className="flex flex-col items-center gap-2">
            <StatusDot status={isConnected ? 'online' : 'offline'} size="sm" />
          </div>
        )}
      </div>
    </aside>
  );
}
