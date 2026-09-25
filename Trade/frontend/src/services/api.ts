const API_BASE = import.meta.env.VITE_API_URL || '/api';

interface RequestOptions {
  method?: string;
  body?: unknown;
  headers?: Record<string, string>;
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(path: string, options: RequestOptions = {}): Promise<T> {
    const { method = 'GET', body, headers = {} } = options;

    const config: RequestInit = {
      method,
      headers: {
        'Content-Type': 'application/json',
        ...headers,
      },
    };

    if (body) {
      config.body = JSON.stringify(body);
    }

    const response = await fetch(`${this.baseUrl}${path}`, config);

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json();
  }

  // Dashboard
  getDashboard() {
    return this.request('/dashboard');
  }

  // Trades
  getTrades(params?: Record<string, string>) {
    const query = params ? '?' + new URLSearchParams(params).toString() : '';
    return this.request(`/trades${query}`);
  }

  getTrade(id: string) {
    return this.request(`/trades/${id}`);
  }

  // Positions
  getPositions() {
    return this.request('/positions');
  }

  // Accounts
  getAccounts() {
    return this.request('/accounts');
  }

  // Strategies
  getStrategies() {
    return this.request('/strategies');
  }

  getStrategy(id: string) {
    return this.request(`/strategies/${id}`);
  }

  // Journal
  getJournalEntries() {
    return this.request('/journal');
  }

  createJournalEntry(data: unknown) {
    return this.request('/journal', { method: 'POST', body: data });
  }

  // Analytics
  getAnalytics() {
    return this.request('/analytics');
  }
}

export const api = new ApiClient(API_BASE);
