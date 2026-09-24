import React from 'react';
import { StatusBadge } from './StatusBadge';

interface EventTimelineItem {
  event_id: string;
  event_type: string;
  component: string;
  level: string;
  message: string;
  timestamp: string;
  details?: Record<string, any>;
}

interface EventTimelineProps {
  events: EventTimelineItem[];
}

export const EventTimeline: React.FC<EventTimelineProps> = ({ events }) => {
  if (!events || events.length === 0) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
        No system events recorded yet.
      </div>
    );
  }

  const formatTime = (ts: string) => {
    try {
      const d = new Date(ts);
      return d.toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
    } catch {
      return ts;
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
      {events.map((evt) => (
        <div
          key={evt.event_id}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '0.65rem 0.85rem',
            borderRadius: 'var(--radius-sm)',
            background: 'rgba(0, 0, 0, 0.25)',
            border: '1px solid var(--border-subtle)',
            fontSize: '0.8125rem',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <span className="mono" style={{ color: 'var(--text-muted)', fontSize: '0.75rem', minWidth: '60px' }}>
              {formatTime(evt.timestamp)}
            </span>
            <StatusBadge status={evt.level} />
            <span className="mono badge badge-neutral" style={{ fontSize: '0.6875rem' }}>
              {evt.component}
            </span>
            <span style={{ color: 'var(--text-primary)' }}>{evt.message}</span>
          </div>
          <span className="mono" style={{ fontSize: '0.6875rem', color: 'var(--accent-primary)' }}>
            {evt.event_type}
          </span>
        </div>
      ))}
    </div>
  );
};
