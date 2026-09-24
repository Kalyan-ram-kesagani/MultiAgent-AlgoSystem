import { 
  ShieldAlert, 
  Activity, 
  Layers, 
  TrendingUp, 
  FlaskConical, 
  FileText, 
  Cpu, 
  Radio,
  Users
} from 'lucide-react';

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  killSwitchActive: boolean;
  onEmergencyClick: () => void;
  systemStatus: {
    environment: string;
    mt5_connected: boolean;
    is_simulation?: boolean;
    gateway_mode?: string;
  };
  isBackendOnline?: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  killSwitchActive,
  onEmergencyClick,
  systemStatus,
  isBackendOnline = true,
}) => {
  const navItems = [
    { id: 'overview', label: 'Overview', icon: Activity },
    { id: 'agents', label: 'Agents', icon: Users },
    { id: 'live', label: 'Live Trading', icon: Radio },
    { id: 'strategies', label: 'Strategies', icon: Layers },
    { id: 'backtesting', label: 'Backtest', icon: TrendingUp },
    { id: 'research', label: 'Research', icon: FlaskConical },
    { id: 'risk', label: 'Risk Center', icon: ShieldAlert },
    { id: 'journal', label: 'Journal', icon: FileText },
    { id: 'monitoring', label: 'Monitoring', icon: Cpu },
  ];


  // Determine truthful MT5 status label and color
  let mt5Label = 'MT5 DISCONNECTED';
  let mt5Color = 'var(--accent-red)';
  let dotClass = 'pulse-dot-red';

  if (!isBackendOnline) {
    mt5Label = 'BACKEND OFFLINE';
    mt5Color = 'var(--accent-red)';
    dotClass = 'pulse-dot-red';
  } else if (systemStatus.mt5_connected) {
    mt5Label = 'MT5 DEMO CONNECTED';
    mt5Color = 'var(--accent-green)';
    dotClass = '';
  } else if (systemStatus.is_simulation) {
    mt5Label = 'SIMULATION GATEWAY';
    mt5Color = 'var(--accent-cyan)';
    dotClass = '';
  }

  return (
    <header style={{
      borderBottom: '1px solid var(--border-color)',
      background: 'rgba(10, 13, 20, 0.85)',
      backdropFilter: 'blur(16px)',
      position: 'sticky',
      top: 0,
      zIndex: 100,
      padding: '0.75rem 1.5rem',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
    }}>
      {/* Brand & Environment */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span style={{ fontSize: '1.4rem' }}>🤖</span>
          <div>
            <h1 style={{ fontSize: '1.05rem', fontWeight: 800, letterSpacing: '-0.02em', margin: 0 }}>
              ANTIGRAVITY <span style={{ color: 'var(--accent-cyan)' }}>ALGO</span>
            </h1>
            <span style={{ fontSize: '0.65rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
              Autonomous Multi-Agent Platform
            </span>
          </div>
        </div>

        <span className={`badge ${isBackendOnline ? 'badge-cyan' : 'badge-red'}`} style={{ marginLeft: '0.5rem' }}>
          {isBackendOnline ? systemStatus.environment : 'OFFLINE'}
        </span>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.75rem' }}>
          <span 
            className={`pulse-dot ${dotClass}`} 
            style={{ backgroundColor: mt5Color }} 
          />
          <span style={{ color: mt5Color, fontWeight: 600 }}>
            {mt5Label}
          </span>
        </div>
      </div>

      {/* Navigation Tabs */}
      <nav style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.4rem',
                padding: '0.5rem 0.85rem',
                fontSize: '0.825rem',
                fontWeight: isActive ? 600 : 500,
                color: isActive ? 'var(--accent-cyan)' : 'var(--text-secondary)',
                background: isActive ? 'rgba(6, 182, 212, 0.1)' : 'transparent',
                border: 'none',
                borderRadius: 'var(--radius-sm)',
                cursor: 'pointer',
                transition: 'all 0.15s ease',
              }}
            >
              <Icon size={16} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>

      {/* Emergency Stop Kill Switch Button */}
      <div>
        <button
          id="kill-switch-button"
          onClick={onEmergencyClick}
          className="btn btn-danger"
          style={{
            animation: killSwitchActive ? 'pulse-red 1s infinite' : 'none',
            fontSize: '0.8rem',
            padding: '0.5rem 1rem',
          }}
        >
          <ShieldAlert size={16} />
          <span>{killSwitchActive ? '🛑 KILL SWITCH ACTIVE' : '🛑 EMERGENCY STOP'}</span>
        </button>
      </div>
    </header>
  );
};
