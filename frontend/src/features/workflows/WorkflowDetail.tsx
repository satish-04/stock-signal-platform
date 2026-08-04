import { useState } from 'react'
import { toast } from 'sonner'
import { useApproveWorkflow, useFailWorkflow, useRetryWorkflow, useWorkflow } from '@/api/queries/workflows'
import { Button } from '@/components/ui/Button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Input } from '@/components/ui/Input'
import { Skeleton } from '@/components/ui/Skeleton'
import { StatusBadge } from '@/components/ui/StatusBadge'
import { WorkflowTimeline } from './WorkflowTimeline'

export function WorkflowDetail({ workflowId }: { workflowId: string }) {
  const { data, isLoading } = useWorkflow(workflowId)
  const [approver, setApprover] = useState('')
  const approve = useApproveWorkflow()
  const retry = useRetryWorkflow()
  const fail = useFailWorkflow()

  if (isLoading || !data) return <Skeleton className="h-64 w-full" />

  return (
    <Card>
      <CardHeader>
        <div>
          <CardTitle>{data.symbol}</CardTitle>
          <p className="mt-1 font-mono text-xs text-text-muted">{data.workflow_id}</p>
        </div>
        <StatusBadge status={data.status} />
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-2 text-sm sm:grid-cols-3">
          <Detail label="Type" value={data.workflow_type} />
          <Detail label="Attempts" value={`${data.attempt_count} / ${data.max_attempts}`} />
          <Detail label="Approval required" value={data.approval_required ? 'Yes' : 'No'} />
          <Detail label="Approved by" value={data.approved_by ?? '—'} />
        </div>

        {data.failure && (
          <div className="rounded-md bg-status-critical/10 p-3 text-sm">
            <p className="font-medium text-status-critical">{data.failure.failure_type}</p>
            <p className="text-text-secondary">{data.failure.message}</p>
          </div>
        )}

        <div className="flex flex-wrap items-end gap-2 border-t border-border pt-3">
          {data.approval_required && !data.approved_by && (
            <div className="flex items-end gap-2">
              <div>
                <label className="mb-1 block text-xs font-medium text-text-secondary">Approver</label>
                <Input value={approver} onChange={(e) => setApprover(e.target.value)} placeholder="your name" className="h-8 w-32" />
              </div>
              <Button
                size="sm"
                disabled={!approver || approve.isPending}
                onClick={() =>
                  approve.mutate(
                    { workflowId, body: { approved_by: approver } },
                    {
                      onSuccess: () => toast.success('Workflow approved'),
                      onError: (err) => toast.error(err instanceof Error ? err.message : 'Approve failed'),
                    },
                  )
                }
              >
                Approve
              </Button>
            </div>
          )}
          {data.failure?.retryable && (
            <Button
              size="sm"
              variant="secondary"
              disabled={retry.isPending}
              onClick={() =>
                retry.mutate(
                  { workflowId },
                  {
                    onSuccess: () => toast.success('Workflow retried'),
                    onError: (err) => toast.error(err instanceof Error ? err.message : 'Retry failed'),
                  },
                )
              }
            >
              Retry
            </Button>
          )}
          {!['COMPLETED', 'FAILED', 'CANCELLED'].includes(data.status) && (
            <Button
              size="sm"
              variant="danger"
              disabled={fail.isPending}
              onClick={() =>
                fail.mutate(
                  { workflowId, body: { failure_type: 'UNKNOWN', message: 'Manually failed from dashboard' } },
                  {
                    onSuccess: () => toast.success('Workflow marked failed'),
                    onError: (err) => toast.error(err instanceof Error ? err.message : 'Fail action failed'),
                  },
                )
              }
            >
              Mark failed
            </Button>
          )}
        </div>

        <div className="border-t border-border pt-4">
          <h3 className="mb-3 text-xs font-semibold uppercase tracking-wide text-text-muted">Timeline</h3>
          <WorkflowTimeline events={data.events} />
        </div>
      </CardContent>
    </Card>
  )
}

function Detail({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md bg-surface-2 p-2">
      <div className="text-xs text-text-muted">{label}</div>
      <div className="font-medium text-text-primary">{value}</div>
    </div>
  )
}
