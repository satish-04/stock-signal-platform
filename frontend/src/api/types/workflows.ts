export type TradingWorkflowStatus =
  | 'CREATED'
  | 'RECOMMENDATION_READY'
  | 'RISK_APPROVED'
  | 'RISK_REJECTED'
  | 'AWAITING_APPROVAL'
  | 'APPROVED'
  | 'INTENT_CREATED'
  | 'EXECUTION_CREATED'
  | 'SUBMISSION_PENDING'
  | 'SUBMITTED'
  | 'PARTIALLY_FILLED'
  | 'FILLED'
  | 'POSITION_RECONCILED'
  | 'EXIT_MONITORING'
  | 'EXIT_SIGNAL_CREATED'
  | 'EXIT_INTENT_CREATED'
  | 'EXIT_EXECUTION_CREATED'
  | 'COMPLETED'
  | 'FAILED'
  | 'CANCELLED'

export type TradingWorkflowType = 'ENTRY' | 'EXIT'

export type WorkflowFailureType =
  | 'VALIDATION'
  | 'RISK_REJECTION'
  | 'DUPLICATE'
  | 'BROKER'
  | 'PERSISTENCE'
  | 'RECONCILIATION'
  | 'CONFIGURATION'
  | 'UNKNOWN'

export interface WorkflowReference {
  recommendation_symbol: string | null
  order_intent_id: string | null
  execution_id: string | null
  position_id: string | null
  exit_signal_id: string | null
  parent_workflow_id: string | null
}

export interface WorkflowFailure {
  failure_type: WorkflowFailureType
  message: string
  retryable: boolean
  occurred_at: string
}

export interface WorkflowEvent {
  event_id: string
  workflow_id: string
  previous_status: TradingWorkflowStatus | null
  new_status: TradingWorkflowStatus
  event_type: string
  message: string | null
  created_at: string
}

export interface TradingWorkflow {
  workflow_id: string
  idempotency_key: string
  workflow_type: TradingWorkflowType
  status: TradingWorkflowStatus
  account_id: string
  symbol: string
  reference: WorkflowReference
  attempt_count: number
  max_attempts: number
  approval_required: boolean
  approved_by: string | null
  approved_at: string | null
  failure: WorkflowFailure | null
  created_at: string
  updated_at: string
  completed_at: string | null
  events: WorkflowEvent[]
}

export interface CreateWorkflowRequest {
  idempotency_key: string
  workflow_type: TradingWorkflowType
  account_id: string
  symbol: string
  parent_workflow_id?: string | null
}

export interface TransitionWorkflowRequest {
  status: string
  message?: string | null
}

export interface ApproveWorkflowRequest {
  approved_by: string
}

export interface FailWorkflowRequest {
  failure_type: string
  message: string
  retryable?: boolean
}
