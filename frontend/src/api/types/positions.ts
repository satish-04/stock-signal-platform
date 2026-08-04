export type PositionSide = 'LONG' | 'SHORT'
export type PositionStatus = 'OPEN' | 'CLOSED'

export interface PositionResponse {
  position_id: string
  account_id: string
  symbol: string
  option_symbol: string
  side: PositionSide
  status: PositionStatus
  quantity: number
  multiplier: number
  average_entry_price: string
  current_mark_price: string | null
  cost_basis: string
  market_value: string | null
  realized_pnl: string
  unrealized_pnl: string | null
  opened_at: string
  updated_at: string
  closed_at: string | null
}

export interface PositionListResponse {
  account_id: string
  count: number
  items: PositionResponse[]
}

export interface PortfolioSummaryResponse {
  account_id: string
  open_positions: number
  closed_positions: number
  total_positions: number
  total_cost_basis: string
  total_market_value: string
  realized_pnl: string
  unrealized_pnl: string
  total_pnl: string
}

export interface MarkPositionRequest {
  mark_price: string
}
