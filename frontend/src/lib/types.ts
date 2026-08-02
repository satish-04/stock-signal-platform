// Types
export interface Signal {
  id: number
  ticker: string
  type: 'bullish' | 'bearish' | 'neutral'
  confidence: number
  price: number
  rsi?: number
  macd?: number
  ema_trend?: string
  action: 'buy' | 'sell' | 'hold'
  quantity?: number
  reason?: string
  created_at: string
}

export interface Option {
  id: number
  ticker: string
  expiry: string
  strike: number
  type: 'call' | 'put'
  bid?: number
  ask?: number
  volume?: number
  open_interest?: number
  iv?: number
  delta?: number
  gamma?: number
  theta?: number
  vega?: number
}

export interface Position {
  id: number
  ticker: string
  quantity: number
  avg_price: number
  current_price?: number
  pnl: number
  pnl_percent: string
  status: 'open' | 'closed'
}

export interface ScannerResult {
  ticker: string
  price: number
  change: string
  volume: string
  signal: 'bullish' | 'bearish' | 'neutral'
  confidence?: number
}

export interface PortfolioSummary {
  total_value: number
  day_pnl: number
  day_pnl_percent: string
  total_trades: number
  win_rate: string
  open_positions: number
}

// Mock data (fallback when API unavailable)
export const mockData: PortfolioSummary = {
  total_value: 152489.37,
  day_pnl: 3456.12,
  day_pnl_percent: '2.9%',
  total_trades: 47,
  win_rate: '68%',
  open_positions: 12
}

// Export api and endpoints from their respective modules for convenience
export { api, endpoints } from './api'
