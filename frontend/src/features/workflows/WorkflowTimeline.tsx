import type { WorkflowEvent } from '@/api/types/workflows'
import { StatusBadge } from '@/components/ui/StatusBadge'
import { formatDateTime } from '@/lib/format'

export function WorkflowTimeline({ events }: { events: WorkflowEvent[] }) {
  if (events.length === 0) {
    return <p className="text-sm text-text-secondary">No events recorded yet.</p>
  }
  return (
    <ol className="space-y-4">
      {events.map((event) => (
        <li key={event.event_id} className="relative pl-5">
          <span className="absolute left-0 top-1.5 h-2 w-2 rounded-full bg-series-1" aria-hidden="true" />
          <div className="flex flex-wrap items-center gap-2">
            <StatusBadge status={event.new_status} />
            <span className="text-xs text-text-muted">{formatDateTime(event.created_at)}</span>
          </div>
          {event.message && <p className="mt-1 text-sm text-text-secondary">{event.message}</p>}
        </li>
      ))}
    </ol>
  )
}
