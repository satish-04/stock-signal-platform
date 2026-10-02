export type OptionsScanStatus = 'running' | 'completed' | 'failed'

export interface ScanStrike {
  strike: number
  volume: number
  /** null when the data provider has blanked open interest, which it does overnight. */
  open_interest: number | null
  last: number
  /** null when the price carries no time value to solve from. */
  implied_volatility: number | null
  premium: number
}

export interface ScanItem {
  symbol: string
  expiry: string
  spot: number
  change_pct: number
  call_volume: number
  put_volume: number
  total_volume: number
  put_call_ratio: number | null
  atm_strike: number
  atm_iv: number | null
  implied_move_pct: number
  top_calls: ScanStrike[]
  top_puts: ScanStrike[]
  last_trade_at: string | null
}

export interface OptionsScanResult {
  /** Every scanned symbol, ordered by contracts traded. */
  items: ScanItem[]
  /** Symbols ranked by at-the-money IV, limited to those above iv_min_volume. */
  top_iv: string[]
  iv_min_volume: number
  skipped: { symbol: string; reason: string }[]
  quotes_as_of: string | null
}

export interface OptionsScan {
  id: string
  status: OptionsScanStatus
  expiry: string
  universe_size: number
  scanned: number
  skipped: number
  started_at: string
  completed_at: string | null
  error: string | null
  progress: { done: number; total: number } | null
  result: OptionsScanResult | null
}

export interface LatestOptionsScanResponse {
  scan: OptionsScan | null
  /** Set when the newest scan has no results, so earlier results can stay on screen. */
  last_completed: OptionsScan | null
}

export interface OptionsScanResponse {
  scan: OptionsScan
}

export interface StartOptionsScanRequest {
  expiry?: string
  symbols?: string[]
}

export interface StartOptionsScanResponse {
  scan: OptionsScan
  started: boolean
}
