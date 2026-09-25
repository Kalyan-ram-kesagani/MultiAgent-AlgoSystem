import type {
  TradingAccount,
  Trade,
  Position,
  Strategy,
  JournalEntry,
  Activity,
  SystemHealthItem,
  DashboardMetrics,
  EquityPoint,
  RiskStatus,
  AnalyticsSummary,
} from '@/types';

// ─── Accounts ───
export const mockAccounts: TradingAccount[] = [
  {
    id: 'acc-1',
    userId: 'user-1',
    broker: 'IC Markets',
    accountName: 'Main Trading',
    accountNumber: '50124821',
    maskedNumber: '••••4821',
    balance: 14118.84,
    equity: 14237.18,
    currency: 'USD',
    status: 'connected',
    accountType: 'live',
    lastSync: new Date(Date.now() - 120000).toISOString(),
    createdAt: '2024-01-15T10:00:00Z',
  },
  {
    id: 'acc-2',
    userId: 'user-1',
    broker: 'IC Markets',
    accountName: 'Testing Account',
    accountNumber: '50127312',
    maskedNumber: '••••7312',
    balance: 5240.0,
    equity: 5240.0,
    currency: 'USD',
    status: 'disconnected',
    accountType: 'demo',
    lastSync: new Date(Date.now() - 480000).toISOString(),
    createdAt: '2024-03-20T10:00:00Z',
  },
  {
    id: 'acc-3',
    userId: 'user-1',
    broker: 'Pepperstone',
    accountName: 'Strategy Testing',
    accountNumber: '88019128',
    maskedNumber: '••••9128',
    balance: 10000.0,
    equity: 10000.0,
    currency: 'USD',
    status: 'disconnected',
    accountType: 'demo',
    lastSync: null,
    createdAt: '2024-06-01T10:00:00Z',
  },
];

// ─── Trades ───
const tradeBase = {
  accountId: 'acc-1',
  commission: -0.7,
  swap: 0,
  createdAt: '2024-09-25T08:00:00Z',
};

export const mockTrades: Trade[] = [
  {
    ...tradeBase,
    id: 'trade-1024',
    symbol: 'EURUSD',
    direction: 'BUY',
    volume: 0.1,
    entryPrice: 1.1732,
    exitPrice: 1.1741,
    stopLoss: 1.1724,
    takeProfit: 1.175,
    entryTime: new Date(Date.now() - 3600000).toISOString(),
    exitTime: new Date(Date.now() - 1800000).toISOString(),
    profitLoss: 9.0,
    status: 'CLOSED',
    result: 'WIN',
    strategyId: 'strat-1',
    strategyName: 'Strategy V1',
    initialRiskPercent: 1.0,
    initialRiskAmount: 14.3,
    riskFreeStatus: 'YES',
    breakEvenPrice: 1.1732,
    riskFreeActivatedTime: new Date(Date.now() - 2400000).toISOString(),
  },
  {
    ...tradeBase,
    id: 'trade-1023',
    symbol: 'GBPUSD',
    direction: 'BUY',
    volume: 0.15,
    entryPrice: 1.3421,
    exitPrice: 1.3445,
    stopLoss: 1.341,
    takeProfit: 1.346,
    entryTime: new Date(Date.now() - 7200000).toISOString(),
    exitTime: new Date(Date.now() - 5400000).toISOString(),
    profitLoss: 36.0,
    status: 'CLOSED',
    result: 'WIN',
    strategyId: 'strat-1',
    strategyName: 'Strategy V1',
    initialRiskPercent: 1.5,
    initialRiskAmount: 16.5,
    riskFreeStatus: 'YES',
    breakEvenPrice: 1.3421,
    riskFreeActivatedTime: new Date(Date.now() - 6000000).toISOString(),
  },
  {
    ...tradeBase,
    id: 'trade-1022',
    symbol: 'USDJPY',
    direction: 'SELL',
    volume: 0.2,
    entryPrice: 149.85,
    exitPrice: 149.92,
    stopLoss: 149.95,
    takeProfit: 149.6,
    entryTime: new Date(Date.now() - 14400000).toISOString(),
    exitTime: new Date(Date.now() - 10800000).toISOString(),
    profitLoss: -9.36,
    status: 'CLOSED',
    result: 'LOSS',
    strategyId: 'strat-1',
    strategyName: 'Strategy V1',
    initialRiskPercent: 1.0,
    initialRiskAmount: 13.4,
    riskFreeStatus: 'NO',
    breakEvenPrice: null,
    riskFreeActivatedTime: null,
  },
  {
    ...tradeBase,
    id: 'trade-1021',
    symbol: 'AUDUSD',
    direction: 'BUY',
    volume: 0.1,
    entryPrice: 0.6412,
    exitPrice: 0.6434,
    stopLoss: 0.6398,
    takeProfit: 0.644,
    entryTime: new Date(Date.now() - 86400000).toISOString(),
    exitTime: new Date(Date.now() - 82800000).toISOString(),
    profitLoss: 22.0,
    status: 'CLOSED',
    result: 'WIN',
    strategyId: 'strat-2',
    strategyName: 'Strategy V2',
    initialRiskPercent: 1.0,
    initialRiskAmount: 14.0,
    riskFreeStatus: 'YES',
    breakEvenPrice: 0.6412,
    riskFreeActivatedTime: new Date(Date.now() - 84600000).toISOString(),
  },
  {
    ...tradeBase,
    id: 'trade-1020',
    symbol: 'EURJPY',
    direction: 'SELL',
    volume: 0.1,
    entryPrice: 162.45,
    exitPrice: 162.38,
    stopLoss: 162.55,
    takeProfit: 162.2,
    entryTime: new Date(Date.now() - 172800000).toISOString(),
    exitTime: new Date(Date.now() - 169200000).toISOString(),
    profitLoss: 4.69,
    status: 'CLOSED',
    result: 'WIN',
    strategyId: 'strat-1',
    strategyName: 'Strategy V1',
    initialRiskPercent: 0.5,
    initialRiskAmount: 6.7,
    riskFreeStatus: 'NO',
    breakEvenPrice: null,
    riskFreeActivatedTime: null,
  },
  {
    ...tradeBase,
    id: 'trade-1019',
    symbol: 'GBPJPY',
    direction: 'BUY',
    volume: 0.05,
    entryPrice: 193.12,
    exitPrice: 193.05,
    stopLoss: 192.95,
    takeProfit: 193.5,
    entryTime: new Date(Date.now() - 259200000).toISOString(),
    exitTime: new Date(Date.now() - 255600000).toISOString(),
    profitLoss: -2.35,
    status: 'CLOSED',
    result: 'LOSS',
    strategyId: 'strat-1',
    strategyName: 'Strategy V1',
    initialRiskPercent: 0.8,
    initialRiskAmount: 5.69,
    riskFreeStatus: 'NO',
    breakEvenPrice: null,
    riskFreeActivatedTime: null,
  },
];

// ─── Positions ───
export const mockPositions: Position[] = [
  {
    id: 'pos-1',
    accountId: 'acc-1',
    symbol: 'EURUSD',
    direction: 'BUY',
    volume: 0.1,
    entryPrice: 1.1728,
    currentPrice: 1.1735,
    stopLoss: 1.172,
    takeProfit: 1.175,
    floatingPL: 7.0,
    openTime: new Date(Date.now() - 900000).toISOString(),
    duration: '15m',
  },
  {
    id: 'pos-2',
    accountId: 'acc-1',
    symbol: 'GBPUSD',
    direction: 'SELL',
    volume: 0.05,
    entryPrice: 1.3442,
    currentPrice: 1.3438,
    stopLoss: 1.3455,
    takeProfit: 1.341,
    floatingPL: 2.0,
    openTime: new Date(Date.now() - 2700000).toISOString(),
    duration: '45m',
  },
];

// ─── Strategies ───
export const mockStrategies: Strategy[] = [
  {
    id: 'strat-1',
    name: 'Momentum Breakout',
    version: 'V1',
    description:
      'Identifies momentum breakouts using a combination of price action and volume analysis on the 1H timeframe. Targets high-probability breakout levels with tight risk management.',
    status: 'active',
    totalTrades: 142,
    winRate: 64.8,
    profitLoss: 2847.5,
    maxDrawdown: 4.2,
    rules: [
      'Trade only during London and New York sessions',
      'Minimum 1:1.5 risk-reward ratio',
      'Maximum 2% risk per trade',
      'Wait for 1H candle close above/below key level',
      'Volume must confirm the breakout',
      'No trading during high-impact news (30 min buffer)',
    ],
    riskParameters: {
      maxRiskPerTrade: '2%',
      maxDailyRisk: '5%',
      maxOpenPositions: 3,
      defaultStopLoss: '15 pips',
      trailingStop: 'Breakeven after 1R',
    },
    createdAt: '2024-01-15T10:00:00Z',
    updatedAt: '2024-09-20T14:30:00Z',
  },
  {
    id: 'strat-2',
    name: 'Range Reversal',
    version: 'V2',
    description:
      'Identifies reversal opportunities at established support and resistance zones using candlestick patterns and RSI divergence on the 4H timeframe.',
    status: 'testing',
    totalTrades: 38,
    winRate: 57.9,
    profitLoss: 412.0,
    maxDrawdown: 3.1,
    rules: [
      'Trade at established S/R zones only',
      'RSI divergence required for entry',
      'Minimum 1:2 risk-reward ratio',
      'Maximum 1.5% risk per trade',
      'Exit partial position at 1R',
    ],
    riskParameters: {
      maxRiskPerTrade: '1.5%',
      maxDailyRisk: '4%',
      maxOpenPositions: 2,
      defaultStopLoss: '20 pips',
      trailingStop: 'Move to breakeven at 1R',
    },
    createdAt: '2024-06-01T10:00:00Z',
    updatedAt: '2024-09-15T09:00:00Z',
  },
  {
    id: 'strat-3',
    name: 'Trend Following',
    version: 'V3',
    description: 'Follows established trends using moving average crossovers and ADX confirmation.',
    status: 'archived',
    totalTrades: 95,
    winRate: 48.4,
    profitLoss: -320.0,
    maxDrawdown: 8.7,
    rules: [
      'Trade in direction of 200 EMA',
      '50/20 EMA crossover for entry',
      'ADX above 25 required',
    ],
    riskParameters: {
      maxRiskPerTrade: '2%',
      maxDailyRisk: '6%',
      maxOpenPositions: 4,
      defaultStopLoss: '25 pips',
      trailingStop: 'ATR trailing',
    },
    createdAt: '2023-08-01T10:00:00Z',
    updatedAt: '2024-02-28T10:00:00Z',
  },
];

// ─── Journal ───
export const mockJournal: JournalEntry[] = [
  {
    id: 'journal-1',
    tradeId: 'trade-1024',
    userId: 'user-1',
    date: new Date(Date.now() - 1800000).toISOString(),
    symbol: 'EURUSD',
    result: 'WIN',
    notes:
      'Clean breakout above the Asian session high. Price consolidated for 30 minutes before breaking out with strong momentum. Entry was at the retest of the breakout level.',
    reason: 'Momentum breakout at Asian session high with volume confirmation',
    lessons: 'Patience paid off — waiting for the retest gave a much better entry than chasing.',
    strategyVersion: 'V1',
    createdAt: new Date(Date.now() - 1800000).toISOString(),
    updatedAt: new Date(Date.now() - 1800000).toISOString(),
  },
  {
    id: 'journal-2',
    tradeId: 'trade-1022',
    userId: 'user-1',
    date: new Date(Date.now() - 10800000).toISOString(),
    symbol: 'USDJPY',
    result: 'LOSS',
    notes:
      'Sold into what looked like resistance but it was a bull flag. Price reversed sharply after a fundamental catalyst. Should have checked the economic calendar.',
    reason: 'Apparent resistance zone with bearish candle',
    lessons: 'Always check economic calendar before entering. The USD data release caused the reversal.',
    strategyVersion: 'V1',
    createdAt: new Date(Date.now() - 10800000).toISOString(),
    updatedAt: new Date(Date.now() - 10800000).toISOString(),
  },
];

// ─── Activities ───
export const mockActivities: Activity[] = [
  {
    id: 'act-1',
    type: 'trade_closed',
    title: 'Trade closed',
    description: 'EURUSD BUY closed +$9.00',
    symbol: 'EURUSD',
    accountId: 'acc-1',
    timestamp: new Date(Date.now() - 120000).toISOString(),
  },
  {
    id: 'act-2',
    type: 'risk_free_activated',
    title: 'Risk-free activated',
    description: 'GBPUSD BUY → SL moved to breakeven',
    symbol: 'GBPUSD',
    accountId: 'acc-1',
    timestamp: new Date(Date.now() - 480000).toISOString(),
  },
  {
    id: 'act-3',
    type: 'trade_opened',
    title: 'Trade opened',
    description: 'EURUSD BUY 0.10 lots at 1.17280',
    symbol: 'EURUSD',
    accountId: 'acc-1',
    timestamp: new Date(Date.now() - 900000).toISOString(),
  },
  {
    id: 'act-4',
    type: 'mt5_synchronized',
    title: 'MT5 synchronized',
    description: 'Account data synchronized successfully',
    symbol: null,
    accountId: 'acc-1',
    timestamp: new Date(Date.now() - 1200000).toISOString(),
  },
  {
    id: 'act-5',
    type: 'trade_closed',
    title: 'Trade closed',
    description: 'GBPUSD BUY closed +$36.00',
    symbol: 'GBPUSD',
    accountId: 'acc-1',
    timestamp: new Date(Date.now() - 5400000).toISOString(),
  },
  {
    id: 'act-6',
    type: 'sl_modified',
    title: 'Stop loss modified',
    description: 'EURUSD BUY SL moved to 1.17320',
    symbol: 'EURUSD',
    accountId: 'acc-1',
    timestamp: new Date(Date.now() - 6000000).toISOString(),
  },
  {
    id: 'act-7',
    type: 'strategy_enabled',
    title: 'Strategy enabled',
    description: 'Strategy V1 activated on account',
    symbol: null,
    accountId: 'acc-1',
    timestamp: new Date(Date.now() - 86400000).toISOString(),
  },
  {
    id: 'act-8',
    type: 'mt5_connected',
    title: 'MT5 connected',
    description: 'MetaTrader 5 connection established',
    symbol: null,
    accountId: 'acc-1',
    timestamp: new Date(Date.now() - 90000000).toISOString(),
  },
];

// ─── Dashboard Metrics ───
export const mockDashboardMetrics: DashboardMetrics = {
  today: {
    pnl: 35.64,
    trades: 3,
    winRate: 66.7,
    wins: 2,
    losses: 1,
    drawdown: 0.9,
  },
  account: {
    balance: 14118.84,
    equity: 14237.18,
    floatingPL: 118.34,
    margin: 234.56,
    freeMargin: 14002.62,
  },
  overall: {
    totalTrades: 142,
    winRate: 64.8,
    totalPnl: 2847.5,
    profitFactor: 1.82,
  },
};

// ─── Equity Curve ───
function generateEquityCurve(): EquityPoint[] {
  const points: EquityPoint[] = [];
  let equity = 10000;
  const startDate = new Date('2024-01-15');
  const today = new Date();
  const dayMs = 86400000;
  let current = startDate.getTime();

  while (current <= today.getTime()) {
    const change = (Math.random() - 0.42) * 80;
    equity = Math.max(equity + change, 8000);
    points.push({
      date: new Date(current).toISOString().split('T')[0],
      equity: Math.round(equity * 100) / 100,
    });
    current += dayMs;
  }

  // Ensure last point matches current balance
  if (points.length > 0) {
    points[points.length - 1].equity = 14118.84;
  }

  return points;
}

export const mockEquityCurve: EquityPoint[] = generateEquityCurve();

// ─── System Health ───
export const mockSystemHealth: SystemHealthItem[] = [
  { name: 'Trading System', status: 'ok' },
  { name: 'MT5 Connection', status: 'ok' },
  { name: 'Market Data', status: 'ok' },
  { name: 'Strategy Engine', status: 'ok' },
  { name: 'Risk Engine', status: 'ok' },
  { name: 'Database', status: 'ok' },
  { name: 'Trade Sync', status: 'ok' },
  { name: 'AI Engine', status: 'coming_soon' },
];

// ─── Risk Status ───
export const mockRiskStatus: RiskStatus = {
  dailyRisk: 2.0,
  dailyLimit: 5.0,
  status: 'within_limit',
};

// ─── Analytics ───
export const mockAnalytics: AnalyticsSummary = {
  winRate: 64.8,
  totalTrades: 142,
  avgWin: 28.4,
  avgLoss: -15.2,
  profitFactor: 1.82,
  bestTrade: 124.5,
  worstTrade: -42.3,
  avgHoldTime: '2h 34m',
  symbolBreakdown: [
    { symbol: 'EURUSD', trades: 48, pnl: 842.5, winRate: 68.8 },
    { symbol: 'GBPUSD', trades: 35, pnl: 612.0, winRate: 62.9 },
    { symbol: 'USDJPY', trades: 28, pnl: 384.0, winRate: 60.7 },
    { symbol: 'AUDUSD', trades: 18, pnl: 520.0, winRate: 72.2 },
    { symbol: 'EURJPY', trades: 13, pnl: 489.0, winRate: 61.5 },
  ],
  strategyBreakdown: [
    { strategy: 'Momentum Breakout V1', trades: 142, pnl: 2847.5, winRate: 64.8 },
    { strategy: 'Range Reversal V2', trades: 38, pnl: 412.0, winRate: 57.9 },
  ],
  monthlyPnl: [
    { month: 'Jan', pnl: 245.0 },
    { month: 'Feb', pnl: 380.0 },
    { month: 'Mar', pnl: -120.0 },
    { month: 'Apr', pnl: 410.0 },
    { month: 'May', pnl: 195.0 },
    { month: 'Jun', pnl: 520.0 },
    { month: 'Jul', pnl: -85.0 },
    { month: 'Aug', pnl: 640.0 },
    { month: 'Sep', pnl: 662.5 },
  ],
};
