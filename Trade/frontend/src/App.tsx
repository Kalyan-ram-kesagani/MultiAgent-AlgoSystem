import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ThemeProvider } from '@/hooks/useTheme';
import { AccountProvider } from '@/hooks/useAccount';
import { AppLayout } from '@/components/layout/AppLayout';
import Dashboard from '@/pages/Dashboard';
import LiveTrading from '@/pages/LiveTrading';
import TradeHistory from '@/pages/TradeHistory';
import Analysis from '@/pages/Analysis';
import Journal from '@/pages/Journal';
import Strategies from '@/pages/Strategies';
import Accounts from '@/pages/Accounts';
import Settings from '@/pages/Settings';

export default function App() {
  return (
    <ThemeProvider>
      <AccountProvider>
        <BrowserRouter>
          <Routes>
            <Route element={<AppLayout />}>
              <Route path="/" element={<Dashboard />} />
              <Route path="/live" element={<LiveTrading />} />
              <Route path="/history" element={<TradeHistory />} />
              <Route path="/analysis" element={<Analysis />} />
              <Route path="/journal" element={<Journal />} />
              <Route path="/strategies" element={<Strategies />} />
              <Route path="/accounts" element={<Accounts />} />
              <Route path="/settings" element={<Settings />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </AccountProvider>
    </ThemeProvider>
  );
}
