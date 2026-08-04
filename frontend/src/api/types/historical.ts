export interface HistoricalBarResponse {
  symbol: string
  timestamp: string
  open: string
  high: string
  low: string
  close: string
  volume: number
}

export interface HistoricalBarsResponse {
  symbol: string
  duration: string
  bar_size: string
  use_rth: boolean
  count: number
  bars: HistoricalBarResponse[]
}
