import React from 'react';
import { useTrading } from '../context/TradingContext';
import {
  WalletCards,
  Plus,
  Server,
  Wifi,
  WifiOff,
  RefreshCw,
  Trash2,
  CheckCircle2,
  Layers,
  ArrowRight,
} from 'lucide-react';
import { TradingAccount } from '../types/trading';

export const AccountsPage: React.FC = () => {
  const {
    accounts,
    selectedAccountId,
    setSelectedAccountId,
    removeAccount,
    setIsAddAccountModalOpen,
    syncNow,
    isSyncing,
    theme,
  } = useTrading();

  const isDark = theme === 'dark';

  const handleDisconnect = async (accountId: string, accountName: string) => {
    if (confirm(`Are you sure you want to disconnect MT5 account "${accountName}"?`)) {
      await removeAccount(accountId);
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in-50 duration-200">
      {/* Header */}
      <div
        className={`flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-3 border-b ${
          isDark ? 'border-slate-800/80' : 'border-slate-200'
        }`}
      >
        <div>
          <div className="flex items-center gap-3">
            <h1 className={`text-xl sm:text-2xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-slate-900'}`}>
              Connected MT5 Accounts
            </h1>
            <span
              className={`text-xs font-mono px-2 py-0.5 rounded border ${
                isDark
                  ? 'text-slate-400 bg-slate-900 border-slate-800'
                  : 'text-slate-600 bg-slate-100 border-slate-200'
              }`}
            >
              {accounts.length} accounts configured
            </span>
          </div>
          <p className={`text-xs mt-1 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
            Manage MetaTrader 5 broker terminals, execution servers, and credential bridges
          </p>
        </div>

        <div className="flex items-center gap-2 sm:gap-3">
          <button
            onClick={syncNow}
            disabled={isSyncing}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md border transition-colors ${
              isDark
                ? 'text-slate-300 bg-slate-800 hover:bg-slate-700 border-slate-700'
                : 'text-slate-700 bg-white hover:bg-slate-100 border-slate-200 shadow-2xs'
            }`}
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isSyncing ? 'animate-spin text-emerald-500' : ''}`} />
            <span>Sync All</span>
          </button>

          <button
            onClick={() => setIsAddAccountModalOpen(true)}
            className="flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-medium text-white bg-emerald-600 hover:bg-emerald-500 rounded-md transition-colors shadow-2xs"
          >
            <Plus className="w-4 h-4" />
            <span>Add MT5 Account</span>
          </button>
        </div>
      </div>

      {/* Accounts List */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {accounts.map((acc: TradingAccount) => {
          const isSelected = selectedAccountId === acc.id;
          const isConnected = acc.status === 'connected';

          return (
            <div
              key={acc.id}
              className={`p-5 rounded-lg border transition-all duration-200 flex flex-col justify-between
                ${
                  isSelected
                    ? isDark
                      ? 'bg-slate-900/90 border-emerald-500/50 shadow-md ring-1 ring-emerald-500/20'
                      : 'bg-white border-emerald-500 shadow-md ring-1 ring-emerald-500/30'
                    : isDark
                    ? 'bg-slate-900/50 border-slate-800 hover:border-slate-700'
                    : 'bg-white border-slate-200 hover:border-slate-300 shadow-xs'
                }
              `}
            >
              <div>
                {/* Account Card Header */}
                <div className="flex items-start justify-between gap-2 mb-3">
                  <div className="flex items-center gap-2.5">
                    <div
                      className={`p-2 rounded-lg border ${
                        isDark
                          ? 'bg-slate-800 border-slate-700 text-slate-200'
                          : 'bg-slate-100 border-slate-200 text-slate-700'
                      }`}
                    >
                      <Server className="w-4 h-4" />
                    </div>
                    <div>
                      <h3 className={`text-sm font-semibold tracking-tight ${isDark ? 'text-white' : 'text-slate-900'}`}>
                        {acc.account_name}
                      </h3>
                      <span className={`text-[11px] font-mono ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                        {acc.broker}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-1.5">
                    <span
                      className={`text-[10px] font-semibold px-2 py-0.5 rounded uppercase tracking-wider ${
                        acc.account_type === 'live'
                          ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30'
                          : 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/30'
                      }`}
                    >
                      {acc.account_type}
                    </span>
                  </div>
                </div>

                {/* Account Details Specs */}
                <div
                  className={`space-y-2 p-3 rounded border text-xs mb-4 ${
                    isDark
                      ? 'bg-slate-950/60 border-slate-800/80'
                      : 'bg-slate-50 border-slate-200'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className={isDark ? 'text-slate-400' : 'text-slate-500'}>Account Number:</span>
                    <span className={`font-mono font-medium ${isDark ? 'text-slate-200' : 'text-slate-800'}`}>
                      {acc.masked_number}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className={isDark ? 'text-slate-400' : 'text-slate-500'}>Server:</span>
                    <span className={`font-mono text-[11px] truncate max-w-[150px] ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>
                      {acc.server}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className={isDark ? 'text-slate-400' : 'text-slate-500'}>Leverage:</span>
                    <span className={`font-mono ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>1:{acc.leverage}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className={isDark ? 'text-slate-400' : 'text-slate-500'}>Status:</span>
                    <span
                      className={`inline-flex items-center gap-1 font-medium ${
                        isConnected ? 'text-emerald-500' : 'text-rose-500'
                      }`}
                    >
                      {isConnected ? (
                        <Wifi className="w-3 h-3 text-emerald-500" />
                      ) : (
                        <WifiOff className="w-3 h-3 text-rose-500" />
                      )}
                      {isConnected ? 'Connected' : 'Disconnected'}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className={isDark ? 'text-slate-400' : 'text-slate-500'}>Last Sync:</span>
                    <span className={`font-mono tabular-nums ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                      {acc.last_sync}
                    </span>
                  </div>
                </div>

                {/* Balance & Equity */}
                <div className="grid grid-cols-2 gap-3 mb-4">
                  <div className={`p-2.5 rounded border ${isDark ? 'bg-slate-800/40 border-slate-800' : 'bg-slate-50 border-slate-200'}`}>
                    <span className={`text-[10px] block mb-0.5 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>Balance</span>
                    <span className={`text-sm font-semibold font-mono tabular-nums ${isDark ? 'text-white' : 'text-slate-900'}`}>
                      ${acc.balance.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                    </span>
                  </div>
                  <div className={`p-2.5 rounded border ${isDark ? 'bg-slate-800/40 border-slate-800' : 'bg-slate-50 border-slate-200'}`}>
                    <span className={`text-[10px] block mb-0.5 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>Equity</span>
                    <span className="text-sm font-semibold font-mono tabular-nums text-emerald-500">
                      ${acc.equity.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                    </span>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className={`flex items-center justify-between pt-3 border-t ${isDark ? 'border-slate-800' : 'border-slate-200'}`}>
                <button
                  onClick={() => handleDisconnect(acc.id, acc.account_name)}
                  className="flex items-center gap-1 text-[11px] text-rose-500 hover:text-rose-600 hover:bg-rose-500/10 px-2 py-1 rounded transition-colors"
                  title="Disconnect MT5 account"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                  <span>Disconnect</span>
                </button>

                {isSelected ? (
                  <div className="flex items-center gap-1.5 px-3 py-1 rounded text-xs font-semibold text-emerald-600 dark:text-emerald-400 bg-emerald-500/10">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>Active Context</span>
                  </div>
                ) : (
                  <button
                    onClick={() => setSelectedAccountId(acc.id)}
                    className={`flex items-center gap-1 px-3 py-1 rounded text-xs font-medium transition-colors ${
                      isDark
                        ? 'text-white bg-slate-800 hover:bg-slate-700'
                        : 'text-slate-800 bg-slate-100 hover:bg-slate-200 border border-slate-200'
                    }`}
                  >
                    <span>Select Account</span>
                    <ArrowRight className={`w-3 h-3 ${isDark ? 'text-slate-400' : 'text-slate-500'}`} />
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
