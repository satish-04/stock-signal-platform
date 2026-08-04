import { cn } from '@/lib/cn'
import { formatStatusLabel, statusTone, TONE_STYLES } from '@/lib/status'

export function StatusBadge({ status, className }: { status: string; className?: string }) {
  const tone = statusTone(status)
  const style = TONE_STYLES[tone]
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-xs font-medium',
        style.bg,
        style.text,
        className,
      )}
    >
      <span className={cn('h-1.5 w-1.5 shrink-0 rounded-full', style.dot)} aria-hidden="true" />
      {formatStatusLabel(status)}
    </span>
  )
}
