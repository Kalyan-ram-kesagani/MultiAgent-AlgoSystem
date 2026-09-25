import React, { useState } from 'react';
import { useTrading } from '../context/TradingContext';
import {
  BookOpen,
  Plus,
  Calendar,
  Sparkles,
  Tag,
  Cpu,
  Layers,
  CheckCircle2,
  XCircle,
  X,
} from 'lucide-react';
import { JournalEntry } from '../types/trading';

export const JournalPage: React.FC = () => {
  const { journalEntries, addJournalEntry, isAllAccounts, activeAccount, selectedAccountId, trades, theme } =
    useTrading();
  const isDark = theme === 'dark';

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedTradeTicket, setSelectedTradeTicket] = useState(trades[0]?.ticket.toString() || '');
  const [notes, setNotes] = useState('');
  const [reason, setReason] = useState('');
  const [lessons, setLessons] = useState('');
  const [tagsInput, setTagsInput] = useState('');

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!notes || !reason) return;

    const matchedTrade = trades.find((t) => t.ticket.toString() === selectedTradeTicket) || trades[0];

    await addJournalEntry({
      trade_id: matchedTrade ? matchedTrade.id : `trd-manual-${Date.now()}`,
      account_id: isAllAccounts ? activeAccount?.id || 'acc-main-01' : selectedAccountId,
      symbol: matchedTrade ? matchedTrade.symbol : 'EURUSD',
      date: new Date().toISOString().slice(0, 10),
      result: matchedTrade ? matchedTrade.status : 'WIN',
      notes,
      reason,
      lessons,
      strategy_version: matchedTrade ? matchedTrade.strategy_name : 'OrderFlow Momentum V2.1',
      tags: tagsInput
        ? tagsInput.split(',').map((t) => t.trim()).filter(Boolean)
        : ['Manual Review'],
    });

    setIsModalOpen(false);
    setNotes('');
    setReason('');
    setLessons('');
    setTagsInput('');
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
              Trading Journal & Review
            </h1>
            <span
              className={`text-xs font-mono px-2 py-0.5 rounded border ${
                isDark
                  ? 'text-slate-400 bg-slate-900 border-slate-800'
                  : 'text-slate-600 bg-slate-100 border-slate-200'
              }`}
            >
              {journalEntries.length} review entries
            </span>
          </div>
          <p className={`text-xs mt-1 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
            Qualitative trade rationales, psychological observations, and behavioral feedback loops
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setIsModalOpen(true)}
            className="flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-medium text-white bg-emerald-600 hover:bg-emerald-500 rounded-md transition-colors shadow-2xs"
          >
            <Plus className="w-4 h-4" />
            <span>New Journal Entry</span>
          </button>
        </div>
      </div>

      {/* Journal Cards Timeline */}
      {journalEntries.length === 0 ? (
        <div
          className={`p-16 text-center rounded-lg border text-xs ${
            isDark
              ? 'border-slate-800 bg-slate-900/40 text-slate-400'
              : 'border-slate-200 bg-white text-slate-600 shadow-xs'
          }`}
        >
          <BookOpen className={`w-8 h-8 mx-auto mb-2 ${isDark ? 'text-slate-600' : 'text-slate-400'}`} />
          <p className={`font-medium ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>No journal logs recorded for this account</p>
          <p className={`mt-1 ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>
            Click "New Journal Entry" to log trade reasoning, screenshots, and behavioral discipline.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {journalEntries.map((entry: JournalEntry) => {
            const isWin = entry.result === 'WIN';
            const isLoss = entry.result === 'LOSS';

            return (
              <div
                key={entry.id}
                className={`p-4 sm:p-5 rounded-lg border transition-all space-y-4 ${
                  isDark
                    ? 'bg-slate-900/60 border-slate-800 hover:border-slate-700/80'
                    : 'bg-white border-slate-200 hover:border-slate-300 shadow-xs'
                }`}
              >
                {/* Entry Header */}
                <div
                  className={`flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b ${
                    isDark ? 'border-slate-800/80' : 'border-slate-100'
                  }`}
                >
                  <div className="flex items-center gap-2.5">
                    <span className={`text-base font-bold font-sans ${isDark ? 'text-white' : 'text-slate-900'}`}>
                      {entry.symbol}
                    </span>
                    <span
                      className={`text-xs font-semibold px-2 py-0.5 rounded ${
                        isWin
                          ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30'
                          : isLoss
                          ? 'bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/30'
                          : isDark
                          ? 'bg-slate-800 text-slate-300'
                          : 'bg-slate-100 text-slate-600'
                      }`}
                    >
                      {entry.result}
                    </span>
                    <span className={`text-xs font-mono ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                      Trade ID: #{entry.trade_id.slice(-6)}
                    </span>
                  </div>

                  <div className={`flex items-center gap-3 text-xs ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                    <div className="flex items-center gap-1">
                      <Calendar className={`w-3.5 h-3.5 ${isDark ? 'text-slate-500' : 'text-slate-400'}`} />
                      <span>{entry.date}</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Cpu className="w-3.5 h-3.5 text-emerald-500" />
                      <span className={isDark ? 'text-slate-300' : 'text-slate-700'}>{entry.strategy_version}</span>
                    </div>
                  </div>
                </div>

                {/* Entry Content Columns */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
                  <div className="space-y-1">
                    <span className={`text-[11px] font-semibold uppercase tracking-wider ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                      Trade Setup & Notes
                    </span>
                    <p className={`leading-relaxed p-3 rounded border ${isDark ? 'text-slate-300 bg-slate-950/40 border-slate-800/60' : 'text-slate-700 bg-slate-50 border-slate-200'}`}>
                      {entry.notes}
                    </p>
                  </div>

                  <div className="space-y-1">
                    <span className={`text-[11px] font-semibold uppercase tracking-wider ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                      Primary Entry Trigger
                    </span>
                    <p className={`leading-relaxed p-3 rounded border ${isDark ? 'text-slate-300 bg-slate-950/40 border-slate-800/60' : 'text-slate-700 bg-slate-50 border-slate-200'}`}>
                      {entry.reason}
                    </p>
                  </div>

                  <div className="space-y-1">
                    <span className={`text-[11px] font-semibold uppercase tracking-wider ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                      Lessons & Behavioral Takeaways
                    </span>
                    <p className={`leading-relaxed p-3 rounded border ${isDark ? 'text-slate-300 bg-slate-950/40 border-slate-800/60' : 'text-slate-700 bg-slate-50 border-slate-200'}`}>
                      {entry.lessons}
                    </p>
                  </div>
                </div>

                {/* Tags and AI Section */}
                <div
                  className={`flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-3 border-t ${
                    isDark ? 'border-slate-800/60' : 'border-slate-100'
                  }`}
                >
                  <div className="flex flex-wrap items-center gap-1.5">
                    {entry.tags.map((t) => (
                      <span
                        key={t}
                        className={`text-[10px] font-mono px-2 py-0.5 rounded border ${
                          isDark
                            ? 'text-slate-400 bg-slate-800/80 border-slate-700/60'
                            : 'text-slate-600 bg-slate-100 border-slate-200'
                        }`}
                      >
                        #{t}
                      </span>
                    ))}
                  </div>

                  {/* Reserved AI Fields (Requirement #15: Mark as coming soon) */}
                  <div className={`flex items-center gap-2 text-[11px] ${isDark ? 'text-slate-500' : 'text-slate-500'}`}>
                    <Sparkles className="w-3.5 h-3.5 text-slate-400" />
                    <span>AI Behavioral Recommendation:</span>
                    <span
                      className={`px-1.5 py-0.5 rounded border ${
                        isDark
                          ? 'bg-slate-800/60 text-slate-400 border-slate-800'
                          : 'bg-slate-100 text-slate-600 border-slate-200'
                      }`}
                    >
                      Coming soon
                    </span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* New Journal Entry Modal */}
      {isModalOpen && (
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
                <BookOpen className="w-5 h-5 text-emerald-500" />
                <h3 className={`text-base font-semibold ${isDark ? 'text-white' : 'text-slate-900'}`}>
                  Log Trading Journal Review
                </h3>
              </div>
              <button
                onClick={() => setIsModalOpen(false)}
                className={`p-1.5 rounded-lg transition-colors ${
                  isDark
                    ? 'text-slate-400 hover:text-white hover:bg-slate-800'
                    : 'text-slate-500 hover:text-slate-900 hover:bg-slate-100'
                }`}
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreate} className="p-4 sm:p-6 space-y-4 text-xs">
              <div>
                <label className={`block font-medium mb-1 ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>
                  Associate with Closed Trade Ticket
                </label>
                <select
                  value={selectedTradeTicket}
                  onChange={(e) => setSelectedTradeTicket(e.target.value)}
                  className={`w-full px-3 py-2 rounded-md border focus:outline-hidden ${
                    isDark
                      ? 'bg-slate-900 border-slate-700 text-white'
                      : 'bg-white border-slate-300 text-slate-900'
                  }`}
                >
                  {trades.map((t) => (
                    <option key={t.ticket} value={t.ticket}>
                      Ticket #{t.ticket} — {t.symbol} {t.direction} ({t.net_pl >= 0 ? '+' : ''}${t.net_pl})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className={`block font-medium mb-1 ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>
                  Detailed Trade Execution Notes *
                </label>
                <textarea
                  rows={3}
                  required
                  placeholder="Describe market context, candle action, support/resistance reaction..."
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  className={`w-full px-3 py-2 rounded-md border focus:outline-hidden transition-colors ${
                    isDark
                      ? 'bg-slate-900 border-slate-700 text-white placeholder-slate-500 focus:border-emerald-500'
                      : 'bg-slate-50 border-slate-300 text-slate-900 placeholder-slate-400 focus:border-emerald-600 focus:bg-white'
                  }`}
                />
              </div>

              <div>
                <label className={`block font-medium mb-1 ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>
                  Primary Entry Reason *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Order block sweep on 15m chart with fair value gap retest"
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  className={`w-full px-3 py-2 rounded-md border focus:outline-hidden transition-colors ${
                    isDark
                      ? 'bg-slate-900 border-slate-700 text-white placeholder-slate-500 focus:border-emerald-500'
                      : 'bg-slate-50 border-slate-300 text-slate-900 placeholder-slate-400 focus:border-emerald-600 focus:bg-white'
                  }`}
                />
              </div>

              <div>
                <label className={`block font-medium mb-1 ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>
                  Lessons Learned
                </label>
                <input
                  type="text"
                  placeholder="e.g. Risk-free breakeven was moved too early, giving trade inadequate room"
                  value={lessons}
                  onChange={(e) => setLessons(e.target.value)}
                  className={`w-full px-3 py-2 rounded-md border focus:outline-hidden transition-colors ${
                    isDark
                      ? 'bg-slate-900 border-slate-700 text-white placeholder-slate-500 focus:border-emerald-500'
                      : 'bg-slate-50 border-slate-300 text-slate-900 placeholder-slate-400 focus:border-emerald-600 focus:bg-white'
                  }`}
                />
              </div>

              <div>
                <label className={`block font-medium mb-1 ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>
                  Tags (Comma separated)
                </label>
                <input
                  type="text"
                  placeholder="e.g. EURUSD, OrderFlow, London Open"
                  value={tagsInput}
                  onChange={(e) => setTagsInput(e.target.value)}
                  className={`w-full px-3 py-2 rounded-md border focus:outline-hidden transition-colors ${
                    isDark
                      ? 'bg-slate-900 border-slate-700 text-white placeholder-slate-500 focus:border-emerald-500'
                      : 'bg-slate-50 border-slate-300 text-slate-900 placeholder-slate-400 focus:border-emerald-600 focus:bg-white'
                  }`}
                />
              </div>

              <div
                className={`flex items-center justify-end gap-3 pt-3 border-t ${
                  isDark ? 'border-slate-800' : 'border-slate-200'
                }`}
              >
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className={`px-4 py-2 font-medium rounded-md transition-colors ${
                    isDark
                      ? 'text-slate-400 hover:text-white bg-slate-800'
                      : 'text-slate-600 hover:text-slate-900 bg-slate-100 border border-slate-200'
                  }`}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 font-medium text-white bg-emerald-600 hover:bg-emerald-500 rounded-md transition-colors shadow-2xs"
                >
                  Save Entry
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
