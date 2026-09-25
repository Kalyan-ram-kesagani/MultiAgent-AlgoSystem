// ─── Account ───
export interface TradingAccount {
  id: string;
  userId: string;
  broker: string;
  accountName: string;
  accountNumber: string;
  maskedNumber: string;
  balance: number;
  equity: number;
  currency: string;
  status: 'connected' | 'disconnected' | 'error';
  accountType: 'live' | 'demo';
  lastSync: string | null;
  createdAt: string;
}

// ─── Trade ───
export type TradeDirection = 'BUY' | 'SELL';
export type TradeStatus = 'OPEN' | 'CLOSED' | 'PENDING' | 'CANCELLED';
export type TradeResult = 'WIN' | 'LOSS' | 'BREAKEVEN' | null;

export interface Trade {
  id: string;
  accountId: string;
  symbol: string;
  direction: TradeDirection;
  volume: number;
  entryPrice: number;
  exitPrice: number | null;
  stopLoss: number | null;
  takeProfit: number | null;
  entryTime: string;
  exitTime: string | null;
  profitLoss: number | null;
  commission: number;
  swap: number;
  status: TradeStatus;
  result: TradeResult;
  strategyId: string | null;
  strategyName: string | null;
  // Risk management
  initialRiskPercent: number | null;
  initialRiskAmount: number | null;
  riskFreeStatus: 'YES' | 'NO' | 'N/A';
  breakEvenPrice: number | null;
  riskFreeActivatedTime: string | null;
  createdAt: string;
}

// ─── Position (Open) ───
export interface Position {
  id: string;
  accountId: string;
  symbol: string;
  direction: TradeDirection;
  volume: number;
  entryPrice: number;
  currentPrice: number;
  stopLoss: number | null;
  takeProfit: number | null;
  floatingPL: number;
  openTime: string;
  duration: string;
}

// ─── Strategy ───
export type StrategyStatus = 'active' | 'testing' | 'archived';

export interface Strategy {
  id: string;
  name: string;
  version: string;
  description: string;
  status: StrategyStatus;
  totalTrades: number;
  winRate: number;
  profitLoss: number;
  maxDrawdown: number;
  rules: string[];
  riskParameters: Record<string, string | number>;
  createdAt: string;
  updatedAt: string;
}

// ─── Journal Entry ───
export interface JournalEntry {
  id: string;
  tradeId: string | null;
  userId: string;
  date: string;
  symbol: string | null;
  result: TradeResult;
  notes: string;
  reason: string;
  lessons: string;
  strategyVersion: string | null;
  createdAt: string;
  updatedAt: string;
}

// ─── Activity ───
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

export interface Activity {
  id: string;
  type: ActivityType;
  title: string;
  description: string;
  symbol: string | null;
  accountId: string | null;
  timestamp: string;
}

// ─── System Health ───
export type HealthStatus = 'ok' | 'warning' | 'error' | 'coming_soon';

export interface SystemHealthItem {
  name: string;
  status: HealthStatus;
  message?: string;
}

// ─── Dashboard ───
export interface DashboardMetrics {
  today: {
    pnl: number;
    trades: number;
    winRate: number;
    wins: number;
    losses: number;
    drawdown: number;
  };
  account: {
    balance: number;
    equity: number;
    floatingPL: number;
    margin: number;
    freeMargin: number;
  };
  overall: {
    totalTrades: number;
    winRate: number;
    totalPnl: number;
    profitFactor: number;
  };
}

export interface EquityPoint {
  date: string;
  equity: number;
}

// ─── Risk ───
export interface RiskStatus {
  dailyRisk: number;
  dailyLimit: number;
  status: 'within_limit' | 'approaching' | 'locked';
}

// ─── Analytics ───
export interface AnalyticsSummary {
  winRate: number;
  totalTrades: number;
  avgWin: number;
  avgLoss: number;
  profitFactor: number;
  bestTrade: number;
  worstTrade: number;
  avgHoldTime: string;
  symbolBreakdown: { symbol: string; trades: number; pnl: number; winRate: number }[];
  strategyBreakdown: { strategy: string; trades: number; pnl: number; winRate: number }[];
  monthlyPnl: { month: string; pnl: number }[];
}

// ─── Common ───
export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

export type DataMode = 'live' | 'demo';
export type Theme = 'dark' | 'light';
