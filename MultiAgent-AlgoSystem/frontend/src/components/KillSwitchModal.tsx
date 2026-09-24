import React, { useState } from 'react';
import { AlertTriangle, X } from 'lucide-react';

interface KillSwitchModalProps {
  isOpen: boolean;
  onClose: () => void;
  isActive: boolean;
  onToggle: (activate: boolean, reason: string) => void;
}

export const KillSwitchModal: React.FC<KillSwitchModalProps> = ({
  isOpen,
  onClose,
  isActive,
  onToggle,
}) => {
  const [reason, setReason] = useState('');

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onToggle(!isActive, reason || (isActive ? 'Manual reset' : 'Emergency Operator Halt'));
    onClose();
  };

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.75)',
      backdropFilter: 'blur(8px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000,
    }}>
      <div className="glass-panel" style={{
        maxWidth: '480px',
        width: '90%',
        backgroundColor: '#111625',
        border: '1px solid rgba(239, 68, 68, 0.4)',
        boxShadow: '0 8px 32px rgba(239, 68, 68, 0.25)',
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <AlertTriangle color="var(--accent-red)" size={24} />
            <h2 style={{ fontSize: '1.15rem', fontWeight: 700, margin: 0 }}>
              {isActive ? 'Reset System Kill Switch' : 'Trigger Emergency Stop'}
            </h2>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
            <X size={20} />
          </button>
        </div>

        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
          {isActive
            ? 'Disengaging the kill switch will allow the Risk Engine to resume evaluating and executing authorized strategy signals.'
            : 'CRITICAL SAFETY ACTION: Engaging the kill switch will IMMEDIATELY halt all new order submissions across all strategies and agents.'}
        </p>

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '1.25rem' }}>
            <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '0.4rem', textTransform: 'uppercase' }}>
              Action Justification / Reason
            </label>
            <input
              type="text"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder={isActive ? "Reason for resumption..." : "e.g., High volatility spike observed"}
              required
              style={{
                width: '100%',
                padding: '0.6rem 0.8rem',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--border-color)',
                background: 'rgba(0, 0, 0, 0.3)',
                color: 'var(--text-primary)',
                fontFamily: 'inherit',
                fontSize: '0.85rem',
              }}
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
            <button type="button" onClick={onClose} className="btn btn-secondary">
              Cancel
            </button>
            <button
              type="submit"
              className={`btn ${isActive ? 'btn-primary' : 'btn-danger'}`}
            >
              {isActive ? 'Confirm Resumption' : 'ENGAGE HARD KILL SWITCH'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
