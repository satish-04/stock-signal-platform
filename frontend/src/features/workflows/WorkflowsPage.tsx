import { WorkflowIcon } from 'lucide-react'
import { useState } from 'react'
import { useWorkflows } from '@/api/queries/workflows'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { EmptyState, ErrorState } from '@/components/ui/EmptyState'
import { SkeletonRows } from '@/components/ui/Skeleton'
import { StatusBadge } from '@/components/ui/StatusBadge'
import { cn } from '@/lib/cn'
import { formatRelativeTime } from '@/lib/format'
import { useUIStore } from '@/store/uiStore'
import { WorkflowDetail } from './WorkflowDetail'

export function WorkflowsPage() {
  const accountId = useUIStore((s) => s.selectedAccountId)
  const { data, isLoading, isError, error } = useWorkflows(accountId)
  const [selectedId, setSelectedId] = useState<string | undefined>()

  if (!accountId) {
    return (
      <div className="space-y-6">
        <h1 className="text-lg font-semibold text-text-primary">Workflows</h1>
        <EmptyState
          icon={WorkflowIcon}
          title="No account selected"
          description="Enter an account ID in the top bar to load trading workflows."
        />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-lg font-semibold text-text-primary">Workflows</h1>
        <p className="text-sm text-text-secondary">Account {accountId}</p>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-[320px_1fr]">
        <Card className="lg:sticky lg:top-0 lg:h-fit">
          <CardHeader>
            <CardTitle>All workflows</CardTitle>
          </CardHeader>
          <CardContent className="max-h-[32rem] overflow-y-auto scroll-thin p-0">
            {isLoading && (
              <div className="p-4">
                <SkeletonRows rows={5} />
              </div>
            )}
            {isError && (
              <div className="p-4">
                <ErrorState message={(error as Error).message} />
              </div>
            )}
            {data && data.length === 0 && (
              <div className="p-4">
                <EmptyState title="No workflows" description="No trading workflows found for this account." />
              </div>
            )}
            <ul className="divide-y divide-border">
              {data?.map((wf) => (
                <li key={wf.workflow_id}>
                  <button
                    onClick={() => setSelectedId(wf.workflow_id)}
                    className={cn(
                      'flex w-full flex-col items-start gap-1 px-4 py-3 text-left hover:bg-hover',
                      selectedId === wf.workflow_id && 'bg-series-1/10',
                    )}
                  >
                    <span className="font-medium text-text-primary">{wf.symbol}</span>
                    <StatusBadge status={wf.status} />
                    <span className="text-xs text-text-muted">{formatRelativeTime(wf.updated_at)}</span>
                  </button>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>

        {selectedId ? (
          <WorkflowDetail workflowId={selectedId} />
        ) : (
          <Card>
            <CardContent>
              <EmptyState title="Select a workflow" description="Choose a workflow from the list to see its status timeline and actions." />
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}
