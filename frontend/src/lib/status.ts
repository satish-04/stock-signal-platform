export type StatusTone = 'good' | 'warning' | 'serious' | 'critical' | 'info' | 'neutral'

export const TONE_STYLES: Record<StatusTone, { dot: string; text: string; bg: string }> = {
  good: { dot: 'bg-status-good', text: 'text-status-good', bg: 'bg-status-good/10' },
  warning: { dot: 'bg-status-warning', text: 'text-status-warning', bg: 'bg-status-warning/10' },
  serious: { dot: 'bg-status-serious', text: 'text-status-serious', bg: 'bg-status-serious/10' },
  critical: { dot: 'bg-status-critical', text: 'text-status-critical', bg: 'bg-status-critical/10' },
  info: { dot: 'bg-series-1', text: 'text-series-1', bg: 'bg-series-1/10' },
  neutral: { dot: 'bg-text-muted', text: 'text-text-secondary', bg: 'bg-text-muted/10' },
}

// One flat lookup covers every enum in the API contract — statuses never collide
// across domains (e.g. "FAILED" always means the same tone everywhere it appears).
const STATUS_TONE: Record<string, StatusTone> = {
  // SignalStatus / SignalDirection
  actionable: 'good',
  review: 'warning',
  rejected: 'critical',
  candidate: 'neutral',
  bullish: 'good',
  bearish: 'critical',
  neutral: 'neutral',

  // PositionStatus / PositionSide
  OPEN: 'info',
  CLOSED: 'neutral',
  LONG: 'good',
  SHORT: 'serious',

  // ExitSignalStatus / ExitUrgency
  CREATED: 'neutral',
  APPROVED: 'info',
  REJECTED: 'critical',
  INTENT_CREATED: 'info',
  SUBMITTED: 'info',
  COMPLETED: 'good',
  FAILED: 'critical',
  NORMAL: 'neutral',
  HIGH: 'warning',
  IMMEDIATE: 'critical',

  // OrderIntentStatus
  PENDING: 'neutral',
  DUPLICATE: 'warning',

  // ExecutionStatus
  SUBMISSION_PENDING: 'neutral',
  ACKNOWLEDGED: 'info',
  PARTIALLY_FILLED: 'warning',
  FILLED: 'good',
  CANCEL_PENDING: 'warning',
  CANCELLED: 'neutral',

  // TradingWorkflowStatus (statuses not already covered above)
  RECOMMENDATION_READY: 'info',
  RISK_APPROVED: 'info',
  RISK_REJECTED: 'critical',
  AWAITING_APPROVAL: 'warning',
  EXECUTION_CREATED: 'info',
  POSITION_RECONCILED: 'good',
  EXIT_MONITORING: 'info',
  EXIT_SIGNAL_CREATED: 'warning',
  EXIT_INTENT_CREATED: 'warning',
  EXIT_EXECUTION_CREATED: 'warning',

  // BackgroundJobStatus
  QUEUED: 'neutral',
  RUNNING: 'info',
  SUCCEEDED: 'good',
  SKIPPED: 'neutral',
  DEAD_LETTER: 'critical',

  // Decisions / risk levels / trade actions
  LOW: 'good',
  MEDIUM: 'warning',
  BUY_CALL: 'good',
  BUY_PUT: 'good',
  SELL_CALL: 'serious',
  SELL_PUT: 'serious',
  HOLD: 'neutral',

  // Health checks
  ok: 'good',
  degraded: 'critical',
}

export function statusTone(status: string): StatusTone {
  return STATUS_TONE[status] ?? 'neutral'
}

export function formatStatusLabel(status: string): string {
  return status
    .toLowerCase()
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}
