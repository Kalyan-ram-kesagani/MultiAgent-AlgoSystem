import {
  TradingAccount,
  Trade,
  OpenPosition,
  SystemActivity,
  Strategy,
  JournalEntry,
  RiskStatus,
  SystemHealthItem,
  EquityDataPoint,
} from '../types/trading';
import {
  MOCK_ACCOUNTS,
  MOCK_TRADES,
  MOCK_OPEN_POSITIONS,
  MOCK_ACTIVITIES,
  MOCK_STRATEGIES,
  MOCK_JOURNAL_ENTRIES,
  MOCK_RISK_STATUS,
  MOCK_SYSTEM_HEALTH,
  generateEquityCurve,
} from '../data/mockData';

// In-memory state storage simulating persistent backend database
let accountsState: TradingAccount[] = [...MOCK_ACCOUNTS];
let tradesState: Trade[] = [...MOCK_TRADES];
let openPositionsState: OpenPosition[] = [...MOCK_OPEN_POSITIONS];
let activitiesState: SystemActivity[] = [...MOCK_ACTIVITIES];
let strategiesState: Strategy[] = [...MOCK_STRATEGIES];
let journalState: JournalEntry[] = [...MOCK_JOURNAL_ENTRIES];

export const TradingAPI = {
  // Accounts
  async getAccounts(): Promise<TradingAccount[]> {
    return [...accountsState];
  },

  async addAccount(accountData: Partial<TradingAccount>): Promise<TradingAccount> {
    const newId = `acc-${Date.now().toString().slice(-6)}`;
    const fullNumber = accountData.account_number || '12345678';
    const masked = `••••${fullNumber.slice(-4)}`;

    const newAcc: TradingAccount = {
      id: newId,
      user_id: 'usr-default-01',
      broker: accountData.broker || 'MetaQuotes Demo',
      account_name: accountData.account_name || 'New MT5 Account',
      account_number: fullNumber,
      masked_number: masked,
      server: accountData.server || 'Demo-Live',
      balance: accountData.balance ?? 10000.0,
      equity: accountData.equity ?? 10000.0,
      margin: 0,
      free_margin: accountData.balance ?? 10000.0,
      margin_level: 0,
      floating_pl: 0,
      currency: accountData.currency || 'USD',
      status: 'connected',
      account_type: accountData.account_type || 'demo',
      leverage: accountData.leverage || 100,
      last_sync: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
      ping_ms: Math.floor(Math.random() * 20) + 10,
      created_at: new Date().toISOString(),
    };

    accountsState.push(newAcc);

    // Record activity
    activitiesState.unshift({
      id: `act-${Date.now()}`,
      account_id: newAcc.id,
      account_name: newAcc.account_name,
      type: 'mt5_connected',
      title: 'MT5 connected',
      description: `Linked ${newAcc.broker} (${newAcc.masked_number})`,
      timestamp: new Date().toISOString(),
      relative_time: 'Just now',
      level: 'success',
    });

    return newAcc;
  },

  async removeAccount(accountId: string): Promise<boolean> {
    const acc = accountsState.find((a) => a.id === accountId);
    accountsState = accountsState.filter((a) => a.id !== accountId);

    if (acc) {
      activitiesState.unshift({
        id: `act-${Date.now()}`,
        account_id: accountId,
        account_name: acc.account_name,
        type: 'mt5_disconnected',
        title: 'MT5 disconnected',
        description: `Unlinked account ${acc.account_name} (${acc.masked_number})`,
        timestamp: new Date().toISOString(),
        relative_time: 'Just now',
        level: 'warning',
      });
    }

    return true;
  },

  async syncAccount(accountId: string): Promise<{ lastSync: string; ping: number }> {
    const nowStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    const ping = Math.floor(Math.random() * 15) + 10;

    accountsState = accountsState.map((acc) => {
      if (accountId === 'all' || acc.id === accountId) {
        return {
          ...acc,
          last_sync: nowStr,
          ping_ms: ping,
          status: 'connected',
        };
      }
      return acc;
    });

    activitiesState.unshift({
      id: `act-${Date.now()}`,
      account_id: accountId === 'all' ? accountsState[0]?.id || '' : accountId,
      account_name: accountId === 'all' ? 'All Accounts' : accountsState.find((a) => a.id === accountId)?.account_name || 'MT5',
      type: 'mt5_synchronized',
      title: 'MT5 synchronized',
      description: `Full state & ticket verification completed (${ping}ms)`,
      timestamp: new Date().toISOString(),
      relative_time: 'Just now',
      level: 'info',
    });

    return { lastSync: nowStr, ping };
  },

  // Trades with strict account isolation
  async getTrades(accountId: string): Promise<Trade[]> {
    if (accountId === 'all') {
      return [...tradesState];
    }
    return tradesState.filter((t) => t.account_id === accountId);
  },

  async getTradeById(tradeId: string): Promise<Trade | undefined> {
    return tradesState.find((t) => t.id === tradeId);
  },

  // Open Positions with strict account isolation
  async getOpenPositions(accountId: string): Promise<OpenPosition[]> {
    if (accountId === 'all') {
      return [...openPositionsState];
    }
    return openPositionsState.filter((p) => p.account_id === accountId);
  },

  async closePosition(positionId: string): Promise<Trade | null> {
    const pos = openPositionsState.find((p) => p.id === positionId);
    if (!pos) return null;

    openPositionsState = openPositionsState.filter((p) => p.id !== positionId);

    const isWin = pos.floating_pl > 0;
    const closedTrade: Trade = {
      id: `trd-${Date.now()}`,
      ticket: pos.ticket,
      account_id: pos.account_id,
      symbol: pos.symbol,
      direction: pos.direction,
      volume: pos.volume,
      entry_price: pos.entry_price,
      exit_price: pos.current_price,
      stop_loss: pos.stop_loss,
      take_profit: pos.take_profit,
      entry_time: pos.entry_time,
      exit_time: new Date().toISOString().replace('T', ' ').slice(0, 19),
      profit_loss: pos.floating_pl,
      commission: -2.5,
      swap: 0,
      net_pl: pos.floating_pl - 2.5,
      status: isWin ? 'WIN' : pos.floating_pl === 0 ? 'BREAKEVEN' : 'LOSS',
      strategy_id: 'strat-01',
      strategy_name: pos.strategy_name,
      initial_risk_percent: 1.0,
      initial_risk_amount: 100.0,
      risk_free_status: pos.risk_free_status,
      break_even_price: pos.break_even_price,
      risk_reward_ratio: Math.abs(pos.floating_pl / 100),
      created_at: new Date().toISOString(),
    };

    tradesState.unshift(closedTrade);

    const acc = accountsState.find((a) => a.id === pos.account_id);
    activitiesState.unshift({
      id: `act-${Date.now()}`,
      account_id: pos.account_id,
      account_name: acc?.account_name || 'MT5',
      type: 'trade_closed',
      title: 'Trade closed',
      description: `${pos.symbol} ${pos.direction} manual close ${pos.floating_pl >= 0 ? '+' : ''}$${pos.floating_pl.toFixed(2)}`,
      timestamp: new Date().toISOString(),
      relative_time: 'Just now',
      symbol: pos.symbol,
      pl: pos.floating_pl,
      level: isWin ? 'success' : 'warning',
    });

    return closedTrade;
  },

  // Recent Activity with strict account isolation
  async getRecentActivity(accountId: string): Promise<SystemActivity[]> {
    if (accountId === 'all') {
      return [...activitiesState];
    }
    return activitiesState.filter((a) => a.account_id === accountId);
  },

  // Strategies
  async getStrategies(accountId: string): Promise<Strategy[]> {
    if (accountId === 'all') {
      return [...strategiesState];
    }
    return strategiesState.filter((s) => s.account_ids.includes(accountId));
  },

  // Journal with strict account isolation
  async getJournalEntries(accountId: string): Promise<JournalEntry[]> {
    if (accountId === 'all') {
      return [...journalState];
    }
    return journalState.filter((j) => j.account_id === accountId);
  },

  async addJournalEntry(entry: Omit<JournalEntry, 'id' | 'created_at' | 'updated_at'>): Promise<JournalEntry> {
    const newEntry: JournalEntry = {
      ...entry,
      id: `jrn-${Date.now().toString().slice(-6)}`,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    journalState.unshift(newEntry);
    return newEntry;
  },

  // Risk Status with strict account isolation
  async getRiskStatus(accountId: string): Promise<RiskStatus> {
    return MOCK_RISK_STATUS[accountId] || MOCK_RISK_STATUS['all'];
  },

  // System Health
  async getSystemHealth(): Promise<SystemHealthItem[]> {
    return [...MOCK_SYSTEM_HEALTH];
  },

  // Equity Curve
  getEquityCurve(accountId: string, timeframe: string): EquityDataPoint[] {
    return generateEquityCurve(accountId, timeframe);
  },
};
