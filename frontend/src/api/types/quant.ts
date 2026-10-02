export type BacktestStrategy = 'ema_cross' | 'rsi_reversion'

export interface BacktestMetrics {
  total_return_pct: number
  cagr_pct: number
  volatility_pct: number
  sharpe: number
  max_drawdown_pct: number
  trades: number
  win_rate_pct: number | null
  exposure_pct: number
}

export interface BacktestRun extends BacktestMetrics {
  params: Record<string, number>
}

export interface WalkForwardWindow {
  train_start: string
  test_start: string
  test_end: string
  params: Record<string, number>
  in_sample_sharpe: number
  out_of_sample_sharpe: number
}

export interface WalkForwardResult {
  train_days: number
  test_days: number
  windows: WalkForwardWindow[]
  out_of_sample: BacktestMetrics
  average_in_sample_sharpe: number
  /** Share of the in-sample Sharpe that survived on unseen data; null when there was none to keep. */
  sharpe_retained_pct: number | null
}

export interface BacktestRequest {
  symbol: string
  strategy: BacktestStrategy
  years: number
  cost_bps: number
}

export interface BacktestResponse {
  symbol: string
  strategy: BacktestStrategy
  bars: number
  start: string
  end: string
  cost_bps: number
  combinations: number
  best: BacktestRun
  top: BacktestRun[]
  benchmark: BacktestMetrics
  equity_curve: { date: string; strategy: number; benchmark: number }[]
  /** null when there is too little history for a training and a test window. */
  walk_forward: WalkForwardResult | null
}

export interface MarketRegimeResponse {
  symbol: string
  as_of: string
  trend: 'up' | 'down' | 'mixed'
  volatility: 'high' | 'normal'
  label: string
  close: number
  sma50: number
  sma200: number
  realized_vol_pct: number
  vol_percentile: number
  scores: { bullish: number; bearish: number }
}
