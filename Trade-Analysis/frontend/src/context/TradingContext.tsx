import React, { createContext, useContext, useState, useEffect, useMemo, useCallback } from 'react';
import {
  TradingAccount,
  Trade,
  OpenPosition,
  SystemActivity,
  Strategy,
  JournalEntry,
  RiskStatus,
  SystemHealthItem,
} from '../types/trading';
import { TradingAPI } from '../services/api';

interface TradingContextType {
  // Accounts
  accounts: TradingAccount[];
  selectedAccountId: string;
  setSelectedAccountId: (id: string) => void;
  activeAccount: TradingAccount | null;
  isAllAccounts: boolean;
  addAccount: (accountData: Partial<TradingAccount>) => Promise<TradingAccount>;
  removeAccount: (accountId: string) => Promise<void>;

  // Data Mode & Sync
  dataMode: 'demo' | 'live';
  setDataMode: (mode: 'demo' | 'live') => void;
  syncStatus: 'connected' | 'disconnected' | 'delayed';
  lastSync: string;
  pingMs: number;
  isSyncing: boolean;
  syncNow: () => Promise<void>;

  // Data collections (Strictly filtered by selectedAccountId)
  trades: Trade[];
  openPositions: OpenPosition[];
  recentActivities: SystemActivity[];
  strategies: Strategy[];
  journalEntries: JournalEntry[];
  riskStatus: RiskStatus;
  systemHealth: SystemHealthItem[];

  // Aggregated/Account Metrics
  metrics: {
    todayPL: number;
    todayTrades: number;
    todayWinRate: number;
    winningTrades: number;
    losingTrades: number;
    balance: number;
    equity: number;
    floatingPL: number;
    margin: number;
    freeMargin: number;
    drawdown: number;
    totalTrades: number;
    overallWinRate: number;
    totalPL: number;
    profitFactor: number;
  };

  // Actions
  closePosition: (positionId: string) => Promise<void>;
  addJournalEntry: (entry: Omit<JournalEntry, 'id' | 'created_at' | 'updated_at'>) => Promise<void>;

  // Modals & Inspection
  selectedTradeForDetails: Trade | null;
  setSelectedTradeForDetails: (trade: Trade | null) => void;
  isAddAccountModalOpen: boolean;
  setIsAddAccountModalOpen: (open: boolean) => void;

  // Theme
  theme: 'dark' | 'light';
  setTheme: (theme: 'dark' | 'light') => void;
  toggleTheme: () => void;
}

const TradingContext = createContext<TradingContextType | undefined>(undefined);

export const TradingProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [accounts, setAccounts] = useState<TradingAccount[]>([]);
  const [selectedAccountId, setSelectedAccountIdState] = useState<string>('acc-main-01');
  const [dataMode, setDataMode] = useState<'demo' | 'live'>('live');
  const [syncStatus, setSyncStatus] = useState<'connected' | 'disconnected' | 'delayed'>('connected');
  const [lastSync, setLastSync] = useState<string>('12:07:42');
  const [pingMs, setPingMs] = useState<number>(18);
  const [isSyncing, setIsSyncing] = useState<boolean>(false);

  const [trades, setTrades] = useState<Trade[]>([]);
  const [openPositions, setOpenPositions] = useState<OpenPosition[]>([]);
  const [recentActivities, setRecentActivities] = useState<SystemActivity[]>([]);
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [journalEntries, setJournalEntries] = useState<JournalEntry[]>([]);
  const [riskStatus, setRiskStatus] = useState<RiskStatus>({
    daily_risk_percent: 2.0,
    daily_limit_percent: 5.0,
    status: 'within_limit',
    current_drawdown: 0.8,
    max_drawdown_limit: 4.0,
    trades_remaining_today: 3,
    max_daily_trades: 5,
  });
  const [systemHealth, setSystemHealth] = useState<SystemHealthItem[]>([]);

  const [selectedTradeForDetails, setSelectedTradeForDetails] = useState<Trade | null>(null);
  const [isAddAccountModalOpen, setIsAddAccountModalOpen] = useState<boolean>(false);
  const [theme, setTheme] = useState<'dark' | 'light'>(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('aegis_theme');
      if (saved === 'light' || saved === 'dark') return saved;
      if (window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches) {
        return 'light';
      }
    }
    return 'dark';
  });

  // Load Accounts initial
  useEffect(() => {
    TradingAPI.getAccounts().then((accs) => {
      setAccounts(accs);
      if (accs.length > 0 && selectedAccountId !== 'all' && !accs.find((a) => a.id === selectedAccountId)) {
        setSelectedAccountIdState(accs[0].id);
      }
    });
    TradingAPI.getSystemHealth().then(setSystemHealth);
  }, []);

  // Theme synchronization with DOM & localStorage
  useEffect(() => {
    const root = document.documentElement;
    if (theme === 'dark') {
      root.classList.add('dark');
      root.classList.remove('light');
    } else {
      root.classList.add('light');
      root.classList.remove('dark');
    }
    try {
      localStorage.setItem('aegis_theme', theme);
    } catch {
      // ignore in iframe
    }
  }, [theme]);

  const toggleTheme = useCallback(() => {
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'));
  }, []);

  // Fetch account-isolated data whenever selectedAccountId changes
  const refreshAccountData = useCallback(async (accId: string) => {
    const [fetchedTrades, fetchedPositions, fetchedActivities, fetchedStrategies, fetchedJournal, fetchedRisk] =
      await Promise.all([
        TradingAPI.getTrades(accId),
        TradingAPI.getOpenPositions(accId),
        TradingAPI.getRecentActivity(accId),
        TradingAPI.getStrategies(accId),
        TradingAPI.getJournalEntries(accId),
        TradingAPI.getRiskStatus(accId),
      ]);

    setTrades(fetchedTrades);
    setOpenPositions(fetchedPositions);
    setRecentActivities(fetchedActivities);
    setStrategies(fetchedStrategies);
    setJournalEntries(fetchedJournal);
    setRiskStatus(fetchedRisk);
  }, []);

  useEffect(() => {
    refreshAccountData(selectedAccountId);
  }, [selectedAccountId, refreshAccountData]);

  // Account selector handler
  const setSelectedAccountId = useCallback(
    (id: string) => {
      setSelectedAccountIdState(id);
      if (id !== 'all') {
        const found = accounts.find((a) => a.id === id);
        if (found) {
          setLastSync(found.last_sync);
          setPingMs(found.ping_ms);
          setSyncStatus(found.status);
          setDataMode(found.account_type);
        }
      } else {
        setSyncStatus('connected');
      }
    },
    [accounts]
  );

  const activeAccount = useMemo(() => {
    if (selectedAccountId === 'all') return null;
    return accounts.find((a) => a.id === selectedAccountId) || null;
  }, [accounts, selectedAccountId]);

  const isAllAccounts = selectedAccountId === 'all';

  // Metrics computation strictly derived from selected data
  const metrics = useMemo(() => {
    if (isAllAccounts) {
      const balance = accounts.reduce((sum, a) => sum + a.balance, 0);
      const equity = accounts.reduce((sum, a) => sum + a.equity, 0);
      const floatingPL = accounts.reduce((sum, a) => sum + a.floating_pl, 0);
      const margin = accounts.reduce((sum, a) => sum + a.margin, 0);
      const freeMargin = accounts.reduce((sum, a) => sum + a.free_margin, 0);

      const totalTrades = trades.length;
      const winningTrades = trades.filter((t) => t.status === 'WIN').length;
      const losingTrades = trades.filter((t) => t.status === 'LOSS').length;
      const overallWinRate = totalTrades > 0 ? Math.round((winningTrades / totalTrades) * 1000) / 10 : 0;
      const totalPL = Math.round(trades.reduce((sum, t) => sum + t.net_pl, 0) * 100) / 100;

      const grossProfit = trades.filter((t) => t.net_pl > 0).reduce((sum, t) => sum + t.net_pl, 0);
      const grossLoss = Math.abs(trades.filter((t) => t.net_pl < 0).reduce((sum, t) => sum + t.net_pl, 0));
      const profitFactor = grossLoss > 0 ? Math.round((grossProfit / grossLoss) * 100) / 100 : grossProfit > 0 ? 9.99 : 0;

      // Today's trades (assuming latest 2 trades represent today's session)
      const todayTradesList = trades.slice(0, 3);
      const todayWins = todayTradesList.filter((t) => t.status === 'WIN').length;
      const todayLosses = todayTradesList.filter((t) => t.status === 'LOSS').length;
      const todayPL = Math.round(todayTradesList.reduce((sum, t) => sum + t.net_pl, 0) * 100) / 100;
      const todayWinRate = todayTradesList.length > 0 ? Math.round((todayWins / todayTradesList.length) * 1000) / 10 : 0;

      return {
        todayPL,
        todayTrades: todayTradesList.length,
        todayWinRate,
        winningTrades,
        losingTrades,
        balance,
        equity,
        floatingPL,
        margin,
        freeMargin,
        drawdown: 1.1,
        totalTrades,
        overallWinRate,
        totalPL,
        profitFactor,
      };
    }

    if (!activeAccount) {
      return {
        todayPL: 0,
        todayTrades: 0,
        todayWinRate: 0,
        winningTrades: 0,
        losingTrades: 0,
        balance: 0,
        equity: 0,
        floatingPL: 0,
        margin: 0,
        freeMargin: 0,
        drawdown: 0,
        totalTrades: 0,
        overallWinRate: 0,
        totalPL: 0,
        profitFactor: 0,
      };
    }

    const totalTrades = trades.length;
    const winningTrades = trades.filter((t) => t.status === 'WIN').length;
    const losingTrades = trades.filter((t) => t.status === 'LOSS').length;
    const overallWinRate = totalTrades > 0 ? Math.round((winningTrades / totalTrades) * 1000) / 10 : 0;
    const totalPL = Math.round(trades.reduce((sum, t) => sum + t.net_pl, 0) * 100) / 100;

    const grossProfit = trades.filter((t) => t.net_pl > 0).reduce((sum, t) => sum + t.net_pl, 0);
    const grossLoss = Math.abs(trades.filter((t) => t.net_pl < 0).reduce((sum, t) => sum + t.net_pl, 0));
    const profitFactor = grossLoss > 0 ? Math.round((grossProfit / grossLoss) * 100) / 100 : grossProfit > 0 ? 9.99 : 0;

    const todayTradesList = trades.slice(0, 2);
    const todayWins = todayTradesList.filter((t) => t.status === 'WIN').length;
    const todayLosses = todayTradesList.filter((t) => t.status === 'LOSS').length;
    const todayPL = Math.round(todayTradesList.reduce((sum, t) => sum + t.net_pl, 0) * 100) / 100;
    const todayWinRate = todayTradesList.length > 0 ? Math.round((todayWins / todayTradesList.length) * 1000) / 10 : 0;

    // Drawdown calculation
    const peak = Math.max(activeAccount.balance, activeAccount.equity);
    const dd = peak > 0 ? Math.round(((peak - activeAccount.equity) / peak) * 1000) / 10 : 0;

    return {
      todayPL,
      todayTrades: todayTradesList.length,
      todayWinRate,
      winningTrades,
      losingTrades,
      balance: activeAccount.balance,
      equity: activeAccount.equity,
      floatingPL: activeAccount.floating_pl,
      margin: activeAccount.margin,
      freeMargin: activeAccount.free_margin,
      drawdown: Math.max(0, dd),
      totalTrades,
      overallWinRate,
      totalPL,
      profitFactor,
    };
  }, [isAllAccounts, activeAccount, accounts, trades]);

  // Sync Now action
  const syncNow = useCallback(async () => {
    setIsSyncing(true);
    try {
      const res = await TradingAPI.syncAccount(selectedAccountId);
      setLastSync(res.lastSync);
      setPingMs(res.ping);
      setSyncStatus('connected');
      const updatedAccounts = await TradingAPI.getAccounts();
      setAccounts(updatedAccounts);
      await refreshAccountData(selectedAccountId);
    } finally {
      setIsSyncing(false);
    }
  }, [selectedAccountId, refreshAccountData]);

  // Close position action
  const closePosition = useCallback(
    async (positionId: string) => {
      await TradingAPI.closePosition(positionId);
      await refreshAccountData(selectedAccountId);
      const updatedAccounts = await TradingAPI.getAccounts();
      setAccounts(updatedAccounts);
    },
    [selectedAccountId, refreshAccountData]
  );

  // Add account action
  const addAccount = useCallback(
    async (accountData: Partial<TradingAccount>) => {
      const newAcc = await TradingAPI.addAccount(accountData);
      const updatedAccounts = await TradingAPI.getAccounts();
      setAccounts(updatedAccounts);
      setSelectedAccountId(newAcc.id);
      return newAcc;
    },
    [setSelectedAccountId]
  );

  // Remove account action
  const removeAccount = useCallback(
    async (accountId: string) => {
      await TradingAPI.removeAccount(accountId);
      const updatedAccounts = await TradingAPI.getAccounts();
      setAccounts(updatedAccounts);
      if (selectedAccountId === accountId) {
        setSelectedAccountId(updatedAccounts[0]?.id || 'all');
      } else {
        await refreshAccountData(selectedAccountId);
      }
    },
    [selectedAccountId, setSelectedAccountId, refreshAccountData]
  );

  // Add journal entry action
  const addJournalEntry = useCallback(
    async (entry: Omit<JournalEntry, 'id' | 'created_at' | 'updated_at'>) => {
      await TradingAPI.addJournalEntry(entry);
      await refreshAccountData(selectedAccountId);
    },
    [selectedAccountId, refreshAccountData]
  );

  return (
    <TradingContext.Provider
      value={{
        accounts,
        selectedAccountId,
        setSelectedAccountId,
        activeAccount,
        isAllAccounts,
        addAccount,
        removeAccount,
        dataMode,
        setDataMode,
        syncStatus,
        lastSync,
        pingMs,
        isSyncing,
        syncNow,
        trades,
        openPositions,
        recentActivities,
        strategies,
        journalEntries,
        riskStatus,
        systemHealth,
        metrics,
        closePosition,
        addJournalEntry,
        selectedTradeForDetails,
        setSelectedTradeForDetails,
        isAddAccountModalOpen,
        setIsAddAccountModalOpen,
        theme,
        setTheme,
        toggleTheme,
      }}
    >
      {children}
    </TradingContext.Provider>
  );
};

export const useTrading = (): TradingContextType => {
  const context = useContext(TradingContext);
  if (!context) {
    throw new Error('useTrading must be used within a TradingProvider');
  }
  return context;
};
