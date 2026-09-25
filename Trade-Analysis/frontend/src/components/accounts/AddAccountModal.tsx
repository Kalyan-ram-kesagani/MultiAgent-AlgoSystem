import React, { useState } from 'react';
import { X, Shield, Plus, Server, Check } from 'lucide-react';
import { useTrading } from '../../context/TradingContext';

export const AddAccountModal: React.FC = () => {
  const { isAddAccountModalOpen, setIsAddAccountModalOpen, addAccount, theme } = useTrading();
  const isDark = theme === 'dark';

  const [broker, setBroker] = useState('');
  const [accountName, setAccountName] = useState('');
  const [accountNumber, setAccountNumber] = useState('');
  const [server, setServer] = useState('');
  const [currency, setCurrency] = useState('USD');
  const [accountType, setAccountType] = useState<'demo' | 'live'>('demo');
  const [leverage, setLeverage] = useState('100');
  const [balance, setBalance] = useState('10000');
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!isAddAccountModalOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!accountName || !accountNumber || !broker) return;

    setIsSubmitting(true);
    try {
      await addAccount({
        broker,
        account_name: accountName,
        account_number: accountNumber,
        server: server || `${broker}-Server01`,
        currency,
        account_type: accountType,
        leverage: Number(leverage),
        balance: Number(balance) || 10000,
        equity: Number(balance) || 10000,
      });
      setIsAddAccountModalOpen(false);
      // Reset form
      setBroker('');
      setAccountName('');
      setAccountNumber('');
      setServer('');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/70 backdrop-blur-xs animate-in fade-in-50 duration-150">
      <div
        className={`w-full max-w-lg rounded-xl border shadow-2xl overflow-hidden transition-colors ${
          isDark
            ? 'border-slate-700 bg-[#0d131f] text-slate-200'
            : 'border-slate-200 bg-white text-slate-800'
        }`}
        onClick={(e) => e.stopPropagation()}
      >
        <div
          className={`flex items-center justify-between px-5 sm:px-6 py-4 border-b ${
            isDark ? 'border-slate-800 bg-slate-900/60' : 'border-slate-200 bg-slate-50'
          }`}
        >
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-500">
              <Server className="w-5 h-5" />
            </div>
            <div>
              <h3 className={`text-base font-semibold ${isDark ? 'text-white' : 'text-slate-900'}`}>
                Add MT5 Account
              </h3>
              <p className={`text-xs ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                Configure MetaTrader 5 execution bridge
              </p>
            </div>
          </div>
          <button
            onClick={() => setIsAddAccountModalOpen(false)}
            className={`p-1.5 rounded-lg transition-colors ${
              isDark
                ? 'text-slate-400 hover:text-white hover:bg-slate-800'
                : 'text-slate-500 hover:text-slate-900 hover:bg-slate-100'
            }`}
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-4 sm:p-6 space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className={`block text-xs font-medium mb-1 ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>
                Account Name *
              </label>
              <input
                type="text"
                required
                placeholder="e.g. Prop Firm Challenge"
                value={accountName}
                onChange={(e) => setAccountName(e.target.value)}
                className={`w-full px-3 py-2 text-xs rounded-md border focus:outline-hidden transition-colors ${
                  isDark
                    ? 'bg-slate-900 border-slate-700 text-white focus:border-emerald-500'
                    : 'bg-slate-50 border-slate-300 text-slate-900 focus:border-emerald-600 focus:bg-white'
                }`}
              />
            </div>
            <div>
              <label className={`block text-xs font-medium mb-1 ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>
                Broker *
              </label>
              <input
                type="text"
                required
                placeholder="e.g. FTMO, IC Markets"
                value={broker}
                onChange={(e) => setBroker(e.target.value)}
                className={`w-full px-3 py-2 text-xs rounded-md border focus:outline-hidden transition-colors ${
                  isDark
                    ? 'bg-slate-900 border-slate-700 text-white focus:border-emerald-500'
                    : 'bg-slate-50 border-slate-300 text-slate-900 focus:border-emerald-600 focus:bg-white'
                }`}
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className={`block text-xs font-medium mb-1 ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>
                Account Login ID *
              </label>
              <input
                type="text"
                required
                placeholder="e.g. 8840219"
                value={accountNumber}
                onChange={(e) => setAccountNumber(e.target.value)}
                className={`w-full px-3 py-2 text-xs font-mono rounded-md border focus:outline-hidden transition-colors ${
                  isDark
                    ? 'bg-slate-900 border-slate-700 text-white focus:border-emerald-500'
                    : 'bg-slate-50 border-slate-300 text-slate-900 focus:border-emerald-600 focus:bg-white'
                }`}
              />
            </div>
            <div>
              <label className={`block text-xs font-medium mb-1 ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>
                Server Name
              </label>
              <input
                type="text"
                placeholder="e.g. FTMO-Server-Demo"
                value={server}
                onChange={(e) => setServer(e.target.value)}
                className={`w-full px-3 py-2 text-xs rounded-md border focus:outline-hidden transition-colors ${
                  isDark
                    ? 'bg-slate-900 border-slate-700 text-white focus:border-emerald-500'
                    : 'bg-slate-50 border-slate-300 text-slate-900 focus:border-emerald-600 focus:bg-white'
                }`}
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div>
              <label className={`block text-xs font-medium mb-1 ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>
                Environment
              </label>
              <select
                value={accountType}
                onChange={(e) => setAccountType(e.target.value as 'demo' | 'live')}
                className={`w-full px-3 py-2 text-xs rounded-md border focus:outline-hidden ${
                  isDark
                    ? 'bg-slate-900 border-slate-700 text-white'
                    : 'bg-white border-slate-300 text-slate-900'
                }`}
              >
                <option value="demo">Demo</option>
                <option value="live">Live Real</option>
              </select>
            </div>
            <div>
              <label className={`block text-xs font-medium mb-1 ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>
                Leverage
              </label>
              <select
                value={leverage}
                onChange={(e) => setLeverage(e.target.value)}
                className={`w-full px-3 py-2 text-xs rounded-md border focus:outline-hidden ${
                  isDark
                    ? 'bg-slate-900 border-slate-700 text-white'
                    : 'bg-white border-slate-300 text-slate-900'
                }`}
              >
                <option value="30">1:30</option>
                <option value="50">1:50</option>
                <option value="100">1:100</option>
                <option value="200">1:200</option>
                <option value="500">1:500</option>
              </select>
            </div>
            <div>
              <label className={`block text-xs font-medium mb-1 ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>
                Balance (USD)
              </label>
              <input
                type="number"
                value={balance}
                onChange={(e) => setBalance(e.target.value)}
                className={`w-full px-3 py-2 text-xs font-mono rounded-md border focus:outline-hidden ${
                  isDark
                    ? 'bg-slate-900 border-slate-700 text-white'
                    : 'bg-white border-slate-300 text-slate-900'
                }`}
              />
            </div>
          </div>

          <div
            className={`p-3 rounded-lg border text-xs flex items-start gap-2.5 ${
              isDark
                ? 'bg-slate-900/50 border-slate-800 text-slate-400'
                : 'bg-slate-50 border-slate-200 text-slate-600'
            }`}
          >
            <Shield className="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" />
            <p>
              Security guarantee: MT5 credentials remain isolated in the backend service layer and are never transmitted to or displayed in the frontend browser environment.
            </p>
          </div>

          <div
            className={`flex items-center justify-end gap-3 pt-3 border-t ${
              isDark ? 'border-slate-800' : 'border-slate-200'
            }`}
          >
            <button
              type="button"
              onClick={() => setIsAddAccountModalOpen(false)}
              className={`px-4 py-2 text-xs font-medium rounded-md transition-colors ${
                isDark
                  ? 'text-slate-400 hover:text-white bg-slate-800'
                  : 'text-slate-600 hover:text-slate-900 bg-slate-100 border border-slate-200'
              }`}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="flex items-center gap-1.5 px-4 py-2 text-xs font-medium text-white bg-emerald-600 hover:bg-emerald-500 rounded-md transition-colors disabled:opacity-50 shadow-2xs"
            >
              <Plus className="w-4 h-4" />
              <span>{isSubmitting ? 'Linking...' : 'Connect Account'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
