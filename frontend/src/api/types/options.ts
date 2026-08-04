export interface RankedOptionResponse {
  symbol: string
  expiry: string
  strike: string
  option_type: 'CALL' | 'PUT'
  bid: string
  ask: string
  last: string
  volume: number
  open_interest: number
  implied_volatility: number
  delta: number
  gamma: number
  theta: number
  vega: number
  score: number
  reasons: string[]
}

export interface BestOptionsResponse {
  symbol: string
  generated_at: string
  best_call: RankedOptionResponse | null
  best_put: RankedOptionResponse | null
}
