import { createContext, useContext, useState, type ReactNode } from 'react';
import type { TradingAccount, DataMode } from '@/types';
import { mockAccounts } from '@/services/mockData';

interface AccountContextValue {
  accounts: TradingAccount[];
  selectedAccount: TradingAccount | null;
  selectedAccountId: string | null; // null = "All Accounts"
  dataMode: DataMode;
  selectAccount: (id: string | null) => void;
  isAllAccounts: boolean;
}

const AccountContext = createContext<AccountContextValue | undefined>(undefined);

export function AccountProvider({ children }: { children: ReactNode }) {
  const [accounts] = useState<TradingAccount[]>(mockAccounts);
  const [selectedAccountId, setSelectedAccountId] = useState<string | null>(
    mockAccounts[0]?.id ?? null
  );

  const selectedAccount =
    selectedAccountId === null
      ? null
      : accounts.find((a) => a.id === selectedAccountId) ?? null;

  const dataMode: DataMode = 'demo'; // Will be 'live' when MT5 is connected

  const selectAccount = (id: string | null) => {
    setSelectedAccountId(id);
  };

  return (
    <AccountContext.Provider
      value={{
        accounts,
        selectedAccount,
        selectedAccountId,
        dataMode,
        selectAccount,
        isAllAccounts: selectedAccountId === null,
      }}
    >
      {children}
    </AccountContext.Provider>
  );
}

export function useAccount() {
  const ctx = useContext(AccountContext);
  if (!ctx) throw new Error('useAccount must be used within AccountProvider');
  return ctx;
}
