export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH'
export type AiTradeAction = 'BUY_CALL' | 'BUY_PUT' | 'SELL_CALL' | 'SELL_PUT' | 'HOLD'

export interface SelectedOptionResponse {
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
  selection_score: number
  selection_reasons: string[]
}

export interface RecommendedTradePlanResponse {
  decision: 'APPROVED' | 'REJECTED'
  side: 'BUY' | 'SELL'
  order_type: 'LIMIT'
  quantity: number
  limit_price: string
  estimated_debit: string
  maximum_loss: string
  stop_price: string
  first_target_price: string
  second_target_price: string
  reward_risk_ratio: string
  account_risk_pct: string
  bid_ask_spread_pct: string
  reasons: string[]
  rejection_reasons: string[]
}

export interface AIRecommendationResponse {
  symbol: string
  action: AiTradeAction
  confidence: number
  risk: RiskLevel
  entry: string
  stop_loss: string
  targets: string[]
  position_size_pct: number
  summary: string
  pros: string[]
  cons: string[]
  reasoning: string
  selected_option: SelectedOptionResponse | null
  trade_plan: RecommendedTradePlanResponse | null
}
