export type BackgroundJobType =
  | 'WORKFLOW_RECONCILIATION'
  | 'EXECUTION_RECONCILIATION'
  | 'POSITION_RECONCILIATION'
  | 'EXIT_MONITORING'
  | 'STALE_WORKFLOW_CLEANUP'

export type BackgroundJobStatus = 'QUEUED' | 'RUNNING' | 'SUCCEEDED' | 'FAILED' | 'SKIPPED' | 'DEAD_LETTER'

export interface WorkerHealthResponse {
  status: 'ok' | 'degraded'
  automation_enabled: boolean
  redis_connected: boolean
  queue_name: string
  safety: {
    trading_mode: string
    manual_approval_required: boolean
    auto_submit: boolean
    order_submission_enabled: boolean
    live_trading_enabled: boolean
  }
}

export interface BackgroundJobResponse {
  job_id: string
  idempotency_key: string
  job_type: BackgroundJobType
  status: BackgroundJobStatus
  scope_id: string | null
  account_id: string | null
  attempt_count: number
  max_attempts: number
  queued_at: string
  started_at: string | null
  completed_at: string | null
  created_at: string
  updated_at: string
  result: Record<string, unknown> | null
  error_type: string | null
  error_message: string | null
  retryable: boolean
}
