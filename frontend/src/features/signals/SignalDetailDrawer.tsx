import type { TradeSignalResponse } from '@/api/types/signals'
import { Drawer } from '@/components/ui/Drawer'
import { StatusBadge } from '@/components/ui/StatusBadge'
import { formatDateTime } from '@/lib/format'

export function SignalDetailDrawer({ signal, onClose }: { signal: TradeSignalResponse | null; onClose: () => void }) {
  return (
    <Drawer open={!!signal} onClose={onClose} title={signal ? `${signal.symbol} signal` : ''}>
      {signal && (
        <div className="space-y-4 text-sm">
          <div className="flex flex-wrap items-center gap-2">
            <StatusBadge status={signal.status} />
            <StatusBadge status={signal.direction} />
            {signal.risk_approved && <StatusBadge status="APPROVED" />}
          </div>

          <dl className="space-y-2">
            <DetailRow label="Strategy" value={signal.strategy} />
            <DetailRow label="Score" value={signal.score.toFixed(2)} />
            <DetailRow label="Created" value={formatDateTime(signal.created_at)} />
            <DetailRow label="Expires" value={formatDateTime(signal.expires_at)} />
            <DetailRow label="Signal ID" value={signal.id} mono />
          </dl>

          <div>
            <h3 className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-text-muted">Details</h3>
            <pre className="scroll-thin max-h-80 overflow-auto rounded-md bg-surface-2 p-3 text-xs text-text-secondary">
              {JSON.stringify(signal.details, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </Drawer>
  )
}

function DetailRow({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="flex items-start justify-between gap-4">
      <dt className="shrink-0 text-text-secondary">{label}</dt>
      <dd className={mono ? 'break-all text-right font-mono text-xs text-text-primary' : 'text-right text-text-primary'}>
        {value}
      </dd>
    </div>
  )
}
