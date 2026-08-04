export type OptionType = 'CALL' | 'PUT'
export type TradeAction = 'BUY_CALL' | 'BUY_PUT' | 'HOLD'
export type TradePlanDecision = 'APPROVED' | 'REJECTED'
export type OrderSide = 'BUY' | 'SELL'
export type OrderType = 'LIMIT'

export interface RiskLimitsRequest {
  account_equity: string
  available_funds: string
  max_risk_per_trade_pct: string
  max_position_value_pct: string
  max_contracts: number
  max_bid_ask_spread_pct: string
  minimum_open_interest: number
  minimum_volume: number
  minimum_reward_risk_ratio: string
}

export interface TradePlanRequest {
  symbol: string
  option_symbol: string
  option_type: OptionType
  expiry: string
  strike: string
  multiplier?: number
  bid: string
  ask: string
  last: string
  volume: number
  open_interest: number
  action: TradeAction
  confidence: string
  stop_loss_pct: string
  first_target_pct: string
  second_target_pct: string
  limits: RiskLimitsRequest
}

export interface TradePlanResponse {
  symbol: string
  option_symbol: string
  decision: TradePlanDecision
  side: OrderSide
  order_type: OrderType
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
