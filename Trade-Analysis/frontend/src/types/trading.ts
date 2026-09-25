export interface TradingAccount {
  id: string;
  user_id: string;
  broker: string;
  account_name: string;
  account_number: string;
  masked_number: string;
  server: string;
  balance: number;
  equity: number;
  margin: number;
  free_margin: number;
  margin_level: number;
  floating_pl: number;
  currency: string;
  status: 'connected' | 'disconnected' | 'delayed';
  account_type: 'live' | 'demo';
  leverage: number;
  last_sync: string;
  ping_ms: number;
  created_at: string;
}

export type RiskFreeStatus = 'YES' | 'NO' | 'N/A';

export interface Trade {
  id: string;
  ticket: number;
  account_id: string;
  symbol: string;
  direction: 'BUY' | 'SELL';
  volume: number;
  entry_price: number;
  exit_price: number;
  stop_loss: number;
  take_profit: number;
  entry_time: string;
  exit_time: string;
  profit_loss: number;
  commission: number;
  swap: number;
  net_pl: number;
  status: 'WIN' | 'LOSS' | 'BREAKEVEN';
  strategy_id: string;
  strategy_name: string;
  // Risk management fields
  initial_risk_percent: number;
  initial_risk_amount: number;
  risk_free_status: RiskFreeStatus;
  break_even_price?: number;
  risk_free_activated_time?: string;
  risk_reward_ratio?: number;
  notes?: string;
  created_at: string;
}

export interface OpenPosition {
  id: string;
  ticket: number;
  account_id: string;
  symbol: string;
  direction: 'BUY' | 'SELL';
  volume: number;
  entry_price: number;
  current_price: number;
  stop_loss: number;
  take_profit: number;
  floating_pl: number;
  duration: string;
  entry_time: string;
  risk_free_status: RiskFreeStatus;
  break_even_price?: number;
  strategy_name: string;
}

export type ActivityType =
  | 'trade_opened'
  | 'trade_closed'
  | 'risk_free_activated'
  | 'sl_modified'
  | 'tp_modified'
  | 'mt5_connected'
  | 'mt5_disconnected'
  | 'mt5_synchronized'
  | 'account_switched'
  | 'strategy_enabled'
  | 'strategy_disabled'
  | 'risk_limit_reached'
  | 'system_warning';

export interface SystemActivity {
  id: string;
  account_id: string;
  account_name: string;
  type: ActivityType;
  title: string;
  description: string;
  timestamp: string;
  relative_time: string;
  symbol?: string;
  pl?: number;
  level?: 'info' | 'success' | 'warning' | 'error';
}

export interface Strategy {
  id: string;
  name: string;
  version: string;
  description: string;
  status: 'active' | 'testing' | 'archived';
  account_ids: string[];
  total_trades: number;
  win_rate: number;
  profit_loss: number;
  max_drawdown: number;
  profit_factor: number;
  created_date: string;
  updated_date: string;
  rules: string[];
  risk_parameters: {
    max_risk_per_trade: string;
    max_daily_drawdown: string;
    rr_target: string;
    breakeven_trigger: string;
  };
  version_history: {
    version: string;
    date: string;
    changes: string;
  }[];
}

export interface JournalEntry {
  id: string;
  trade_id: string;
  account_id: string;
  symbol: string;
  date: string;
  result: 'WIN' | 'LOSS' | 'BREAKEVEN';
  notes: string;
  reason: string;
  lessons: string;
  strategy_version: string;
  tags: string[];
  created_at: string;
  updated_at: string;
  // Reserved for AI Phase
  ai_detected_reason?: string;
  ai_recommendation?: string;
  ai_modification?: string;
}

export interface RiskStatus {
  daily_risk_percent: number;
  daily_limit_percent: number;
  status: 'within_limit' | 'approaching' | 'locked';
  current_drawdown: number;
  max_drawdown_limit: number;
  trades_remaining_today: number;
  max_daily_trades: number;
}

export interface SystemHealthItem {
  id: string;
  name: string;
  status: 'ok' | 'warning' | 'error' | 'coming_soon';
  latency_ms?: number;
  message?: string;
}

export interface EquityDataPoint {
  date: string;
  timestamp: number;
  balance: number;
  equity: number;
  drawdown: number;
  pl: number;
}
