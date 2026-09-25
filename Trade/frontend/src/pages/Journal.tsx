import { useState } from 'react';
import { mockJournal } from '@/services/mockData';
import { useAccount } from '@/hooks/useAccount';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { EmptyState } from '@/components/ui/EmptyState';
import { formatDateTime, formatRelativeTime } from '@/utils/format';
import { BookOpen, Plus, Sparkles, Calendar, Tag, BookMarked } from 'lucide-react';

export default function Journal() {
  const { isAllAccounts, selectedAccount } = useAccount();
  const [showForm, setShowForm] = useState(false);
  const entries = mockJournal;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold text-text-primary">Trading Journal</h1>
          <p className="text-sm text-text-secondary mt-0.5">
            {entries.length} entries · {isAllAccounts ? 'All Accounts' : selectedAccount?.accountName}
          </p>
        </div>
        <Button icon={<Plus size={14} />} onClick={() => setShowForm(!showForm)}>
          New Entry
        </Button>
      </div>

      {/* New Entry Form */}
      {showForm && (
        <div className="card animate-slide-up space-y-4">
          <h3 className="text-sm font-medium text-text-primary">New Journal Entry</h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs text-text-muted mb-1.5">Symbol</label>
              <input
                type="text"
                placeholder="e.g. EURUSD"
                className="w-full px-3 py-2 text-sm bg-surface border border-border rounded-lg text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent"
              />
            </div>
            <div>
              <label className="block text-xs text-text-muted mb-1.5">Result</label>
              <select className="w-full px-3 py-2 text-sm bg-surface border border-border rounded-lg text-text-primary focus:outline-none focus:border-accent">
                <option value="">Select</option>
                <option value="WIN">WIN</option>
                <option value="LOSS">LOSS</option>
                <option value="BREAKEVEN">BREAKEVEN</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs text-text-muted mb-1.5">Trade Reason</label>
            <input
              type="text"
              placeholder="Why did you take this trade?"
              className="w-full px-3 py-2 text-sm bg-surface border border-border rounded-lg text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent"
            />
          </div>

          <div>
            <label className="block text-xs text-text-muted mb-1.5">Notes</label>
            <textarea
              rows={3}
              placeholder="Describe the trade setup, execution, and outcome..."
              className="w-full px-3 py-2 text-sm bg-surface border border-border rounded-lg text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent resize-none"
            />
          </div>

          <div>
            <label className="block text-xs text-text-muted mb-1.5">Lessons Learned</label>
            <textarea
              rows={2}
              placeholder="What did you learn from this trade?"
              className="w-full px-3 py-2 text-sm bg-surface border border-border rounded-lg text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent resize-none"
            />
          </div>

          <div className="flex items-center justify-end gap-2">
            <Button variant="ghost" onClick={() => setShowForm(false)}>Cancel</Button>
            <Button>Save Entry</Button>
          </div>
        </div>
      )}

      {/* Journal Entries */}
      {entries.length === 0 ? (
        <EmptyState
          icon={<BookOpen size={40} />}
          title="No journal entries yet"
          description="Start documenting your trades to improve your trading performance."
          action={<Button icon={<Plus size={14} />} onClick={() => setShowForm(true)}>New Entry</Button>}
        />
      ) : (
        <div className="space-y-3">
          {entries.map((entry) => (
            <div key={entry.id} className="card hover:border-border transition-colors">
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2">
                  {entry.symbol && (
                    <span className="text-sm font-bold text-text-primary">{entry.symbol}</span>
                  )}
                  {entry.result && (
                    <Badge variant={entry.result === 'WIN' ? 'success' : entry.result === 'LOSS' ? 'danger' : 'neutral'}>
                      {entry.result}
                    </Badge>
                  )}
                  {entry.strategyVersion && (
                    <Badge variant="neutral">{entry.strategyVersion}</Badge>
                  )}
                </div>
                <div className="flex items-center gap-1 text-text-muted">
                  <Calendar size={12} />
                  <span className="text-[11px]">{formatRelativeTime(entry.date)}</span>
                </div>
              </div>

              {entry.reason && (
                <div className="mb-3">
                  <div className="flex items-center gap-1.5 mb-1">
                    <Tag size={11} className="text-text-muted" />
                    <span className="text-[10px] font-semibold uppercase tracking-wider text-text-muted">Reason</span>
                  </div>
                  <p className="text-sm text-text-secondary">{entry.reason}</p>
                </div>
              )}

              {entry.notes && (
                <div className="mb-3">
                  <div className="flex items-center gap-1.5 mb-1">
                    <BookMarked size={11} className="text-text-muted" />
                    <span className="text-[10px] font-semibold uppercase tracking-wider text-text-muted">Notes</span>
                  </div>
                  <p className="text-sm text-text-secondary leading-relaxed">{entry.notes}</p>
                </div>
              )}

              {entry.lessons && (
                <div className="mb-3">
                  <div className="flex items-center gap-1.5 mb-1">
                    <Sparkles size={11} className="text-accent" />
                    <span className="text-[10px] font-semibold uppercase tracking-wider text-text-muted">Lessons</span>
                  </div>
                  <p className="text-sm text-text-secondary leading-relaxed">{entry.lessons}</p>
                </div>
              )}

              {/* Future AI Fields */}
              <div className="mt-3 pt-3 border-t border-border/50 flex flex-wrap gap-3">
                {['AI Detected Reason', 'AI Recommendation', 'AI Modification'].map((label) => (
                  <span key={label} className="flex items-center gap-1 text-[10px] text-text-muted">
                    <Sparkles size={9} />
                    {label} · Coming Soon
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
