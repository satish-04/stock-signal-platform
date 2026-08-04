export type SignalStatus = 'rejected' | 'review' | 'actionable' | 'candidate'
export type SignalDirection = 'bullish' | 'bearish' | 'neutral'

export interface TradeSignalResponse {
  id: string
  symbol: string
  direction: SignalDirection
  strategy: string
  score: number
  status: SignalStatus
  details: Record<string, unknown>
  risk_approved: boolean
  expires_at: string
  created_at: string
}

export interface SignalListResponse {
  items: TradeSignalResponse[]
  count: number
}

export interface TechnicalSignalResponse {
  symbol: string
  direction: SignalDirection
  confidence: number
  trend_score: number
  momentum_score: number
  volatility_score: number
  volume_score: number
  reasons: string[]
  warnings: string[]
}
