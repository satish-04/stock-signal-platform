import { useState } from 'react'
import { useWorkerHealth } from '@/api/queries/health'
import { useBackgroundJob } from '@/api/queries/jobs'
import { Button } from '@/components/ui/Button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { ErrorState } from '@/components/ui/EmptyState'
import { Input } from '@/components/ui/Input'
import { Skeleton } from '@/components/ui/Skeleton'
import { StatusBadge } from '@/components/ui/StatusBadge'
import { formatDateTime } from '@/lib/format'

export function JobsPage() {
  const { data: health, isLoading } = useWorkerHealth()
  const [input, setInput] = useState('')
  const [jobId, setJobId] = useState<string | undefined>()
  const job = useBackgroundJob(jobId)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-lg font-semibold text-text-primary">Background jobs</h1>
        <p className="text-sm text-text-secondary">Worker automation health and individual job status lookup.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Worker health</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading && <Skeleton className="h-32 w-full" />}
          {health && (
            <div className="grid grid-cols-2 gap-3 text-sm sm:grid-cols-3">
              <Detail label="Status" value={<StatusBadge status={health.status} />} />
              <Detail label="Automation" value={health.automation_enabled ? 'Enabled' : 'Disabled'} />
              <Detail label="Redis" value={health.redis_connected ? 'Connected' : 'Disconnected'} />
              <Detail label="Queue" value={health.queue_name} />
              <Detail label="Manual approval" value={health.safety.manual_approval_required ? 'Required' : 'Not required'} />
              <Detail label="Auto submit" value={health.safety.auto_submit ? 'On' : 'Off'} />
              <Detail label="Order submission" value={health.safety.order_submission_enabled ? 'Enabled' : 'Disabled'} />
              <Detail label="Live trading" value={health.safety.live_trading_enabled ? 'Enabled' : 'Disabled'} />
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Look up job by ID</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <form
            className="flex gap-2"
            onSubmit={(e) => {
              e.preventDefault()
              setJobId(input.trim() || undefined)
            }}
          >
            <Input value={input} onChange={(e) => setInput(e.target.value)} placeholder="Job UUID" className="font-mono text-xs" />
            <Button type="submit">Look up</Button>
          </form>
          {job.isError && <ErrorState message={(job.error as Error).message} />}
          {job.data && (
            <div className="grid grid-cols-2 gap-2 text-sm sm:grid-cols-3">
              <Detail label="Type" value={job.data.job_type} />
              <Detail label="Status" value={<StatusBadge status={job.data.status} />} />
              <Detail label="Attempts" value={`${job.data.attempt_count} / ${job.data.max_attempts}`} />
              <Detail label="Queued" value={formatDateTime(job.data.queued_at)} />
              <Detail label="Completed" value={formatDateTime(job.data.completed_at)} />
              <Detail label="Retryable" value={job.data.retryable ? 'Yes' : 'No'} />
              {job.data.error_message && <Detail label="Error" value={job.data.error_message} />}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

function Detail({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="rounded-md bg-surface-2 p-2">
      <div className="text-xs text-text-muted">{label}</div>
      <div className="font-medium text-text-primary">{value}</div>
    </div>
  )
}
