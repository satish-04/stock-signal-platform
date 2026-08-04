export type ExitReason =
  | 'STOP_LOSS'
  | 'FIRST_TARGET'
  | 'SECOND_TARGET'
  | 'TRAILING_STOP'
  | 'MAX_HOLDING_TIME'
  | 'EXPIRATION_RISK'
  | 'STALE_MARK'

export type ExitSignalStatus =
  | 'CREATED'
  | 'APPROVED'
  | 'REJECTED'
  | 'INTENT_CREATED'
  | 'SUBMITTED'
  | 'COMPLETED'
  | 'FAILED'

export type ExitUrgency = 'NORMAL' | 'HIGH' | 'IMMEDIATE'

export interface MonitorRequest {
  position_id: string
  account_id: string
  symbol: string
  option_symbol: string
  quantity: number
  multiplier: number
  average_entry_price: string
  current_mark_price: string
  highest_mark_price: string
  opened_at: string
  evaluated_at: string
  mark_updated_at: string
  expiration?: string | null
  first_target_already_taken?: boolean
}

export interface ExitSignalResponse {
  exit_signal_id: string
  idempotency_key: string
  position_id: string
  account_id: string
  symbol: string
  option_symbol: string
  reason: ExitReason
  urgency: ExitUrgency
  status: ExitSignalStatus
  requested_quantity: number
  mark_price: string
  trigger_price: string | null
  created_at: string
  updated_at: string
  explanations: string[]
  rejection_reasons: string[]
}
