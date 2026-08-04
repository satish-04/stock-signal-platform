export interface TechnicalAnalysisResponse {
  symbol: string
  duration: string
  bar_size: string
  use_rth: boolean
  ema_9: number | null
  ema_20: number | null
  ema_50: number | null
  ema_200: number | null
  sma_20: number | null
  rsi_14: number | null
  macd: number | null
  macd_signal: number | null
  macd_histogram: number | null
  atr_14: number | null
  vwap: number | null
  bollinger_upper: number | null
  bollinger_middle: number | null
  bollinger_lower: number | null
}
