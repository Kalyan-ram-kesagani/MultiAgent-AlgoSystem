/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState } from 'react';
import { TradingProvider, useTrading } from './context/TradingContext';
import { Sidebar, PageId } from './components/layout/Sidebar';
import { TopNavbar } from './components/layout/TopNavbar';
import { DashboardPage } from './pages/DashboardPage';
import { LiveTradingPage } from './pages/LiveTradingPage';
import { TradeHistoryPage } from './pages/TradeHistoryPage';
import { AnalysisPage } from './pages/AnalysisPage';
import { JournalPage } from './pages/JournalPage';
import { StrategiesPage } from './pages/StrategiesPage';
import { AccountsPage } from './pages/AccountsPage';
import { SettingsPage } from './pages/SettingsPage';
import { TradeDetailsModal } from './components/trades/TradeDetailsModal';
import { AddAccountModal } from './components/accounts/AddAccountModal';

const AppContent: React.FC = () => {
  const [currentPage, setCurrentPage] = useState<PageId>('dashboard');
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const { selectedTradeForDetails, setSelectedTradeForDetails, theme } = useTrading();

  const renderPage = () => {
    switch (currentPage) {
      case 'dashboard':
        return <DashboardPage />;
      case 'live-trading':
        return <LiveTradingPage />;
      case 'trade-history':
        return <TradeHistoryPage />;
      case 'analysis':
        return <AnalysisPage />;
      case 'journal':
        return <JournalPage />;
      case 'strategies':
        return <StrategiesPage />;
      case 'accounts':
        return <AccountsPage />;
      case 'settings':
        return <SettingsPage />;
      default:
        return <DashboardPage />;
    }
  };

  return (
    <div
      className={`min-h-screen ${
        theme === 'dark'
          ? 'dark bg-[#080d16] text-slate-100'
          : 'light bg-slate-50 text-slate-800'
      } flex transition-colors duration-200`}
    >
      {/* Sidebar Navigation */}
      <Sidebar
        currentPage={currentPage}
        setCurrentPage={setCurrentPage}
        isCollapsed={isSidebarCollapsed}
        setIsCollapsed={setIsSidebarCollapsed}
        isMobileOpen={isMobileMenuOpen}
        setIsMobileOpen={setIsMobileMenuOpen}
      />

      {/* Main Content Area */}
      <div
        className={`flex-1 flex flex-col min-w-0 transition-all duration-200 ease-in-out ${
          isSidebarCollapsed ? 'lg:pl-18' : 'lg:pl-64'
        }`}
      >
        {/* Top Navbar */}
        <TopNavbar
          onOpenMobileMenu={() => setIsMobileMenuOpen(true)}
          isSidebarCollapsed={isSidebarCollapsed}
        />

        {/* Page Content Viewport */}
        <main className="flex-1 p-3.5 sm:p-5 lg:p-7 max-w-7xl w-full mx-auto pb-16 sm:pb-8">
          {renderPage()}
        </main>
      </div>

      {/* Modals & Inspection Drawers */}
      <TradeDetailsModal
        trade={selectedTradeForDetails}
        onClose={() => setSelectedTradeForDetails(null)}
      />
      <AddAccountModal />
    </div>
  );
};

export default function App() {
  return (
    <TradingProvider>
      <AppContent />
    </TradingProvider>
  );
}
