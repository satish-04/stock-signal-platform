import type { LucideIcon } from 'lucide-react'
import { InboxIcon } from 'lucide-react'

export function EmptyState({
  icon: Icon = InboxIcon,
  title,
  description,
  action,
}: {
  icon?: LucideIcon
  title: string
  description?: string
  action?: React.ReactNode
}) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 px-4 py-12 text-center">
      <Icon className="h-8 w-8 text-text-muted" aria-hidden="true" />
      <p className="text-sm font-medium text-text-primary">{title}</p>
      {description && <p className="max-w-sm text-sm text-text-secondary">{description}</p>}
      {action}
    </div>
  )
}

export function ErrorState({ message }: { message: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 px-4 py-12 text-center">
      <p className="text-sm font-medium text-status-critical">Something went wrong</p>
      <p className="max-w-sm text-sm text-text-secondary">{message}</p>
    </div>
  )
}
