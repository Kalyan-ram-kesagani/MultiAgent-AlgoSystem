import React from 'react';

interface StatusBadgeProps {
  status: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status = 'UNKNOWN' }) => {
  let badgeClass = 'badge-neutral';
  const s = String(status).toUpperCase();

  if (['LIVE', 'APPROVED', 'VALIDATED', 'FILLED', 'OPERATIONAL', 'HEALTHY', 'CONNECTED', 'IDLE', 'SUCCESS'].includes(s)) {
    badgeClass = 'badge-green';
  } else if (['REJECTED', 'FAILED', 'EMERGENCY_STOPPED', 'CRITICAL', 'SUSPENDED', 'ERROR', 'DISCONNECTED', 'HALTED', 'ENGAGED'].includes(s)) {
    badgeClass = 'badge-red';
  } else if (['PENDING', 'TESTING', 'DRAFT', 'PAPER', 'WARNING', 'FLAGGED', 'WAITING', 'STARTING'].includes(s)) {
    badgeClass = 'badge-amber';
  } else if (['WORKING', 'RUNNING', 'SIMULATION', 'ARMED'].includes(s)) {
    badgeClass = 'badge-cyan';
  }

  return <span className={`badge ${badgeClass}`}>{status}</span>;
};

