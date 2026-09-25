import React, { useState, useRef, useEffect } from 'react';
import {
  ChevronDown,
  Plus,
  RefreshCw,
  Sun,
  Moon,
  Menu,
  Check,
  Layers,
  Wifi,
  WifiOff,
  AlertTriangle,
} from 'lucide-react';
import { useTrading } from '../../context/TradingContext';

interface TopNavbarProps {
  onOpenMobileMenu: () => void;
  isSidebarCollapsed: boolean;
}

export const TopNavbar: React.FC<TopNavbarProps> = ({
  onOpenMobileMenu,
  isSidebarCollapsed,
}) => {
  const {
    accounts,
    selectedAccountId,
    setSelectedAccountId,
    activeAccount,
    isAllAccounts,
    dataMode,
    setDataMode,
    syncStatus,
    lastSync,
    pingMs,
    isSyncing,
    syncNow,
    theme,
    toggleTheme,
    setIsAddAccountModalOpen,
  } = useTrading();

  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <header
      className={`sticky top-0 z-30 flex items-center justify-between h-16 px-3 sm:px-5 md:px-6 border-b transition-colors duration-200
        ${
          theme === 'dark'
            ? 'bg-[#0b101b]/95 border-slate-800/80 text-slate-200'
            : 'bg-white/95 border-slate-200 text-slate-800 shadow-xs'
        } backdrop-blur-md
      `}
    >
      {/* Left Zone: Mobile toggle + Breadcrumb / Account Context */}
      <div className="flex items-center gap-2 sm:gap-3 min-w-0">
        <button
          onClick={onOpenMobileMenu}
          className={`p-2 -ml-1 rounded-lg lg:hidden transition-colors ${
            theme === 'dark'
              ? 'text-slate-400 hover:text-white hover:bg-slate-800'
              : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
          }`}
          aria-label="Open menu"
        >
          <Menu className="w-5 h-5" />
        </button>

        {/* Account Selector Dropdown */}
        <div className="relative" ref={dropdownRef}>
          <button
            onClick={() => setIsDropdownOpen(!isDropdownOpen)}
            className={`flex items-center gap-2 sm:gap-2.5 px-2.5 sm:px-3 py-1.5 rounded-lg border text-left transition-all ${
              theme === 'dark'
                ? 'bg-slate-900/80 hover:bg-slate-800/80 border-slate-700/70 text-slate-200'
                : 'bg-slate-50 hover:bg-slate-100 border-slate-300 text-slate-800'
            } focus:outline-hidden focus:ring-1 focus:ring-emerald-500/50 max-w-[210px] sm:max-w-xs`}
            aria-expanded={isDropdownOpen}
          >
            <div
              className={`flex items-center justify-center w-7 h-7 rounded-md border shrink-0 ${
                theme === 'dark'
                  ? 'bg-slate-800 border-slate-700 text-slate-300'
                  : 'bg-white border-slate-200 text-slate-700'
              }`}
            >
              {isAllAccounts ? (
                <Layers className="w-4 h-4 text-emerald-500" />
              ) : (
                <span className="text-[11px] font-mono font-bold text-emerald-500">
                  {activeAccount?.account_name.slice(0, 2).toUpperCase() || 'MT'}
                </span>
              )}
            </div>

            <div className="flex flex-col text-left truncate min-w-0">
              <div className="flex items-center gap-1.5 truncate">
                <span
                  className={`text-xs font-semibold tracking-tight truncate ${
                    theme === 'dark' ? 'text-white' : 'text-slate-900'
                  }`}
                >
                  {isAllAccounts ? 'All Accounts' : activeAccount?.account_name}
                </span>
                <span className="flex w-1.5 h-1.5 rounded-full bg-emerald-500 shrink-0" />
              </div>
              <span
                className={`text-[10px] font-mono truncate ${
                  theme === 'dark' ? 'text-slate-400' : 'text-slate-500'
                }`}
              >
                {isAllAccounts
                  ? `${accounts.length} connected`
                  : `MT5 ${activeAccount?.masked_number}`}
              </span>
            </div>

            <ChevronDown
              className={`w-4 h-4 shrink-0 transition-transform duration-200 ml-1 ${
                theme === 'dark' ? 'text-slate-400' : 'text-slate-500'
              } ${isDropdownOpen ? 'rotate-180' : ''}`}
            />
          </button>

          {/* Account Dropdown Menu */}
          {isDropdownOpen && (
            <div
              className={`absolute left-0 top-full mt-1.5 w-72 rounded-lg border shadow-xl z-50 p-1.5 animate-in fade-in-50 zoom-in-95 duration-100 ${
                theme === 'dark'
                  ? 'bg-[#0f172a] border-slate-700/80 text-slate-200'
                  : 'bg-white border-slate-200 text-slate-800'
              }`}
            >
              <div
                className={`px-2 py-1.5 text-[10px] font-semibold tracking-wider uppercase ${
                  theme === 'dark' ? 'text-slate-400' : 'text-slate-500'
                }`}
              >
                Select Account
              </div>

              {/* Individual Accounts */}
              <div className="space-y-0.5 max-h-60 overflow-y-auto">
                {accounts.map((acc) => {
                  const isSelected = selectedAccountId === acc.id;
                  return (
                    <button
                      key={acc.id}
                      onClick={() => {
                        setSelectedAccountId(acc.id);
                        setIsDropdownOpen(false);
                      }}
                      className={`flex items-center justify-between w-full px-2.5 py-2 text-xs rounded-md transition-colors text-left ${
                        isSelected
                          ? theme === 'dark'
                            ? 'bg-slate-800 text-white font-medium'
                            : 'bg-emerald-50 text-emerald-950 font-medium'
                          : theme === 'dark'
                          ? 'text-slate-300 hover:bg-slate-800/60 hover:text-white'
                          : 'text-slate-700 hover:bg-slate-100 hover:text-slate-900'
                      }`}
                    >
                      <div className="flex items-center gap-2.5 min-w-0">
                        <span
                          className={`w-2 h-2 rounded-full shrink-0 ${
                            acc.status === 'connected' ? 'bg-emerald-500' : 'bg-rose-500'
                          }`}
                        />
                        <div className="flex flex-col truncate">
                          <span
                            className={`font-medium truncate ${
                              theme === 'dark' ? 'text-white' : 'text-slate-900'
                            }`}
                          >
                            {acc.account_name}
                          </span>
                          <span
                            className={`text-[10px] font-mono ${
                              theme === 'dark' ? 'text-slate-400' : 'text-slate-500'
                            }`}
                          >
                            MT5 {acc.masked_number} · {acc.account_type.toUpperCase()}
                          </span>
                        </div>
                      </div>
                      <div className="flex items-center gap-2 shrink-0">
                        <span
                          className={`text-[11px] font-mono tabular-nums ${
                            theme === 'dark' ? 'text-slate-300' : 'text-slate-600'
                          }`}
                        >
                          ${acc.balance.toLocaleString('en-US', { minimumFractionDigits: 0 })}
                        </span>
                        {isSelected && <Check className="w-3.5 h-3.5 text-emerald-500" />}
                      </div>
                    </button>
                  );
                })}
              </div>

              {/* All Accounts Option */}
              <div
                className={`pt-1.5 mt-1.5 border-t ${
                  theme === 'dark' ? 'border-slate-700/60' : 'border-slate-200'
                }`}
              >
                <button
                  onClick={() => {
                    setSelectedAccountId('all');
                    setIsDropdownOpen(false);
                  }}
                  className={`flex items-center justify-between w-full px-2.5 py-2 text-xs rounded-md transition-colors text-left ${
                    isAllAccounts
                      ? theme === 'dark'
                        ? 'bg-slate-800 text-white font-medium'
                        : 'bg-emerald-50 text-emerald-950 font-medium'
                      : theme === 'dark'
                      ? 'text-slate-300 hover:bg-slate-800/60 hover:text-white'
                      : 'text-slate-700 hover:bg-slate-100 hover:text-slate-900'
                  }`}
                >
                  <div className="flex items-center gap-2.5">
                    <Layers className="w-4 h-4 text-emerald-500" />
                    <div className="flex flex-col">
                      <span
                        className={`font-medium ${
                          theme === 'dark' ? 'text-white' : 'text-slate-900'
                        }`}
                      >
                        All Accounts
                      </span>
                      <span
                        className={`text-[10px] ${
                          theme === 'dark' ? 'text-slate-400' : 'text-slate-500'
                        }`}
                      >
                        Combined portfolio metrics
                      </span>
                    </div>
                  </div>
                  {isAllAccounts && <Check className="w-3.5 h-3.5 text-emerald-500" />}
                </button>
              </div>

              {/* Add Account Action */}
              <div
                className={`pt-1 mt-1 border-t ${
                  theme === 'dark' ? 'border-slate-700/60' : 'border-slate-200'
                }`}
              >
                <button
                  onClick={() => {
                    setIsDropdownOpen(false);
                    setIsAddAccountModalOpen(true);
                  }}
                  className="flex items-center gap-2 w-full px-2.5 py-2 text-xs font-medium text-emerald-600 dark:text-emerald-400 hover:bg-emerald-50 dark:hover:bg-emerald-500/10 rounded-md transition-colors"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>Add MT5 Account</span>
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Right Zone: Data Mode badge + MT5 Sync Status + Sync Now + Theme */}
      <div className="flex items-center gap-1.5 sm:gap-3">
        {/* Data Mode Indicator */}
        <div className="hidden sm:flex items-center">
          {dataMode === 'live' ? (
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[11px] font-medium bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
              <span>LIVE DATA</span>
            </div>
          ) : (
            <div
              className="flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[11px] font-medium bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/30 cursor-pointer"
              title="Sample data — not real trading results"
              onClick={() => setDataMode('live')}
            >
              <AlertTriangle className="w-3 h-3 text-amber-500" />
              <span>DEMO MODE</span>
            </div>
          )}
        </div>

        {/* MT5 Status + Last Sync */}
        <div
          className={`hidden md:flex items-center gap-2 px-2.5 py-1 rounded-md border text-xs ${
            theme === 'dark'
              ? 'bg-slate-900/60 border-slate-800'
              : 'bg-slate-50 border-slate-200'
          }`}
        >
          {syncStatus === 'connected' ? (
            <div className="flex items-center gap-1.5">
              <Wifi className="w-3.5 h-3.5 text-emerald-500" />
              <span
                className={`text-[11px] font-medium ${
                  theme === 'dark' ? 'text-slate-200' : 'text-slate-700'
                }`}
              >
                Connected
              </span>
              <span className={theme === 'dark' ? 'text-slate-600' : 'text-slate-300'}>·</span>
              <span
                className={`text-[10px] font-mono tabular-nums ${
                  theme === 'dark' ? 'text-slate-400' : 'text-slate-500'
                }`}
              >
                Last sync: {lastSync}
              </span>
            </div>
          ) : syncStatus === 'delayed' ? (
            <div className="flex items-center gap-1.5 text-amber-500">
              <AlertTriangle className="w-3.5 h-3.5 text-amber-500" />
              <span className="text-[11px] font-medium">Data delayed</span>
              <span className="text-slate-400">·</span>
              <span className="text-[10px] font-mono tabular-nums">7m ago</span>
            </div>
          ) : (
            <div className="flex items-center gap-1.5 text-rose-500">
              <WifiOff className="w-3.5 h-3.5 text-rose-500" />
              <span className="text-[11px] font-medium">Disconnected</span>
              <span className="text-slate-400">·</span>
              <span className="text-[10px] font-mono tabular-nums">4m ago</span>
            </div>
          )}

          {pingMs > 0 && syncStatus === 'connected' && (
            <span
              className={`text-[10px] font-mono tabular-nums ${
                theme === 'dark' ? 'text-slate-500' : 'text-slate-400'
              }`}
            >
              ({pingMs}ms)
            </span>
          )}
        </div>

        {/* Sync Now Button */}
        <button
          onClick={syncNow}
          disabled={isSyncing}
          className={`flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-medium rounded-md border transition-colors disabled:opacity-50 ${
            theme === 'dark'
              ? 'text-slate-300 hover:text-white bg-slate-800/80 hover:bg-slate-700/80 border-slate-700'
              : 'text-slate-700 hover:text-slate-900 bg-white hover:bg-slate-100 border-slate-300 shadow-2xs'
          }`}
          title="Synchronize MT5 accounts and positions"
        >
          <RefreshCw
            className={`w-3.5 h-3.5 ${
              isSyncing ? 'animate-spin text-emerald-500' : ''
            }`}
          />
          <span className="hidden sm:inline">{isSyncing ? 'Syncing...' : 'Sync'}</span>
        </button>

        {/* Theme Toggle Button */}
        <button
          onClick={toggleTheme}
          className={`p-2 rounded-md border transition-all cursor-pointer ${
            theme === 'dark'
              ? 'text-slate-300 hover:text-white bg-slate-800/80 border-slate-700 hover:bg-slate-700'
              : 'text-slate-700 hover:text-slate-950 bg-white border-slate-300 hover:bg-slate-100 shadow-2xs'
          }`}
          title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
          aria-label="Toggle theme"
        >
          {theme === 'dark' ? (
            <Sun className="w-4 h-4 text-amber-400" />
          ) : (
            <Moon className="w-4 h-4 text-slate-700" />
          )}
        </button>
      </div>
    </header>
  );
};
