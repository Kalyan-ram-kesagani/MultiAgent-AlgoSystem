import React from 'react';
import {
  LayoutDashboard,
  Activity,
  History,
  BarChart3,
  BookOpen,
  Cpu,
  WalletCards,
  Settings,
  ChevronLeft,
  ChevronRight,
  ShieldCheck,
  Radio,
  X,
} from 'lucide-react';
import { useTrading } from '../../context/TradingContext';

export type PageId =
  | 'dashboard'
  | 'live-trading'
  | 'trade-history'
  | 'analysis'
  | 'journal'
  | 'strategies'
  | 'accounts'
  | 'settings';

interface SidebarProps {
  currentPage: PageId;
  setCurrentPage: (page: PageId) => void;
  isCollapsed: boolean;
  setIsCollapsed: (collapsed: boolean) => void;
  isMobileOpen: boolean;
  setIsMobileOpen: (open: boolean) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentPage,
  setCurrentPage,
  isCollapsed,
  setIsCollapsed,
  isMobileOpen,
  setIsMobileOpen,
}) => {
  const { syncStatus, isAllAccounts, activeAccount, theme } = useTrading();

  const navGroups = [
    {
      group: 'TRADING SYSTEM',
      items: [
        { id: 'dashboard' as PageId, label: 'Dashboard', icon: LayoutDashboard },
        { id: 'live-trading' as PageId, label: 'Live Trading', icon: Activity },
        { id: 'trade-history' as PageId, label: 'Trade History', icon: History },
      ],
    },
    {
      group: 'ANALYTICS',
      items: [
        { id: 'analysis' as PageId, label: 'Analysis', icon: BarChart3 },
        { id: 'journal' as PageId, label: 'Journal', icon: BookOpen },
        { id: 'strategies' as PageId, label: 'Strategies', icon: Cpu },
      ],
    },
    {
      group: 'SYSTEM',
      items: [
        { id: 'accounts' as PageId, label: 'Accounts', icon: WalletCards },
        { id: 'settings' as PageId, label: 'Settings', icon: Settings },
      ],
    },
  ];

  const handleNavClick = (id: PageId) => {
    setCurrentPage(id);
    setIsMobileOpen(false);
  };

  return (
    <>
      {/* Mobile Backdrop */}
      {isMobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm lg:hidden transition-opacity"
          onClick={() => setIsMobileOpen(false)}
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={`fixed top-0 bottom-0 left-0 z-50 flex flex-col border-r transition-all duration-200 ease-in-out ${
          theme === 'dark'
            ? 'bg-[#0d131f] text-slate-300 border-slate-800/80'
            : 'bg-white text-slate-700 border-slate-200 shadow-md'
        } ${isCollapsed ? 'w-18' : 'w-64'} ${
          isMobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        }`}
      >
        {/* Brand Header */}
        <div
          className={`flex items-center justify-between h-16 px-4 border-b ${
            theme === 'dark' ? 'border-slate-800/80' : 'border-slate-200'
          }`}
        >
          <div className="flex items-center gap-3 overflow-hidden">
            <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-500 shrink-0">
              <ShieldCheck className="w-5 h-5" />
            </div>
            {!isCollapsed && (
              <div className="flex flex-col truncate">
                <span
                  className={`text-sm font-semibold tracking-tight ${
                    theme === 'dark' ? 'text-white' : 'text-slate-900'
                  }`}
                >
                  AEGIS TRADER
                </span>
                <span
                  className={`text-[10px] uppercase tracking-wider ${
                    theme === 'dark' ? 'text-slate-400' : 'text-slate-500'
                  }`}
                >
                  Automated Execution
                </span>
              </div>
            )}
          </div>

          {/* Mobile Close Button */}
          <button
            onClick={() => setIsMobileOpen(false)}
            className={`p-1.5 rounded-md lg:hidden transition-colors ${
              theme === 'dark'
                ? 'text-slate-400 hover:text-white hover:bg-slate-800'
                : 'text-slate-500 hover:text-slate-900 hover:bg-slate-100'
            }`}
            aria-label="Close menu"
          >
            <X className="w-5 h-5" />
          </button>

          {/* Desktop Collapse Toggle */}
          <button
            onClick={() => setIsCollapsed(!isCollapsed)}
            className={`hidden p-1.5 rounded-md lg:flex items-center justify-center transition-colors ${
              theme === 'dark'
                ? 'text-slate-400 hover:text-white hover:bg-slate-800/60'
                : 'text-slate-500 hover:text-slate-900 hover:bg-slate-100'
            }`}
            title={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {isCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </button>
        </div>

        {/* Navigation Groups */}
        <div className="flex-1 px-2.5 py-4 space-y-6 overflow-y-auto">
          {navGroups.map((group) => (
            <div key={group.group} className="space-y-1">
              {!isCollapsed ? (
                <div
                  className={`px-2.5 mb-2 text-[10px] font-semibold tracking-wider uppercase ${
                    theme === 'dark' ? 'text-slate-500' : 'text-slate-400'
                  }`}
                >
                  {group.group}
                </div>
              ) : (
                <div
                  className={`w-6 h-px mx-auto my-3 ${
                    theme === 'dark' ? 'bg-slate-800' : 'bg-slate-200'
                  }`}
                />
              )}

              {group.items.map((item) => {
                const Icon = item.icon;
                const isActive = currentPage === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => handleNavClick(item.id)}
                    title={isCollapsed ? item.label : undefined}
                    className={`flex items-center w-full gap-3 px-3 py-2.5 text-xs font-medium rounded-md transition-colors relative cursor-pointer ${
                      isActive
                        ? theme === 'dark'
                          ? 'bg-slate-800/90 text-white shadow-xs font-semibold'
                          : 'bg-emerald-50 text-emerald-950 font-semibold shadow-2xs'
                        : theme === 'dark'
                        ? 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
                        : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                    } ${isCollapsed ? 'justify-center px-0' : ''}`}
                  >
                    {isActive && (
                      <span className="absolute left-0 top-1.5 bottom-1.5 w-1 bg-emerald-500 rounded-r-full" />
                    )}
                    <Icon
                      className={`w-4 h-4 shrink-0 ${
                        isActive
                          ? 'text-emerald-500'
                          : theme === 'dark'
                          ? 'text-slate-400'
                          : 'text-slate-500'
                      }`}
                    />
                    {!isCollapsed && <span className="truncate">{item.label}</span>}
                  </button>
                );
              })}
            </div>
          ))}
        </div>

        {/* Bottom System Status */}
        <div
          className={`p-3 border-t ${
            theme === 'dark'
              ? 'border-slate-800/80 bg-slate-900/40'
              : 'border-slate-200 bg-slate-50'
          }`}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="relative flex w-2 h-2">
                <span className="absolute inline-flex w-full h-full rounded-full opacity-75 animate-ping bg-emerald-400" />
                <span className="relative inline-flex w-2 h-2 rounded-full bg-emerald-500" />
              </span>
              {!isCollapsed && (
                <div className="flex flex-col">
                  <span
                    className={`text-[11px] font-medium ${
                      theme === 'dark' ? 'text-slate-200' : 'text-slate-800'
                    }`}
                  >
                    System Online
                  </span>
                  <span
                    className={`text-[10px] flex items-center gap-1 ${
                      theme === 'dark' ? 'text-slate-400' : 'text-slate-500'
                    }`}
                  >
                    <Radio className="w-3 h-3 text-emerald-500" />
                    {syncStatus === 'connected' ? 'MT5 Connected' : 'MT5 Disconnected'}
                  </span>
                </div>
              )}
            </div>

            {!isCollapsed && (
              <span
                className={`text-[10px] font-mono tabular-nums ${
                  theme === 'dark' ? 'text-slate-400' : 'text-slate-500'
                }`}
              >
                {isAllAccounts ? 'Multi-Acc' : activeAccount?.masked_number}
              </span>
            )}
          </div>
        </div>
      </aside>
    </>
  );
};
