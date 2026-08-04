import type { LucideIcon } from 'lucide-react'
import { cn } from '@/lib/cn'

export function StatTile({
  label,
  value,
  icon: Icon,
  tone = 'neutral',
  hint,
}: {
  label: string
  value: string
  icon?: LucideIcon
  tone?: 'good' | 'critical' | 'neutral'
  hint?: string
}) {
  const toneClass = tone === 'good' ? 'text-success-text' : tone === 'critical' ? 'text-status-critical' : 'text-text-primary'
  return (
    <div className="rounded-lg border border-border bg-surface p-4">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium uppercase tracking-wide text-text-muted">{label}</span>
        {Icon && <Icon className="h-4 w-4 text-text-muted" aria-hidden="true" />}
      </div>
      <p className={cn('mt-2 tabular-nums text-2xl font-semibold', toneClass)}>{value}</p>
      {hint && <p className="mt-1 text-xs text-text-secondary">{hint}</p>}
    </div>
  )
}
