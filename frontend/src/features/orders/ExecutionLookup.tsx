import { useState } from 'react'
import { useExecution } from '@/api/queries/orderExecutions'
import { Button } from '@/components/ui/Button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { ErrorState } from '@/components/ui/EmptyState'
import { Input } from '@/components/ui/Input'
import { StatusBadge } from '@/components/ui/StatusBadge'
import { formatCurrency, formatDateTime } from '@/lib/format'

export function ExecutionLookup() {
  const [input, setInput] = useState('')
  const [executionId, setExecutionId] = useState<string | undefined>()
  const { data, isError, error } = useExecution(executionId)

  return (
    <Card>
      <CardHeader>
        <CardTitle>Look up execution by ID</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <form
          className="flex gap-2"
          onSubmit={(e) => {
            e.preventDefault()
            setExecutionId(input.trim() || undefined)
          }}
        >
          <Input value={input} onChange={(e) => setInput(e.target.value)} placeholder="Execution UUID" className="font-mono text-xs" />
          <Button type="submit">Look up</Button>
        </form>
        {isError && <ErrorState message={(error as Error).message} />}
        {data && (
          <dl className="space-y-1.5 text-sm">
            <Row label="Status" value={<StatusBadge status={data.status} />} />
            <Row label="Symbol" value={`${data.symbol} / ${data.option_symbol}`} />
            <Row label="Side" value={data.side} />
            <Row label="Filled" value={`${data.filled_quantity} / ${data.requested_quantity}`} />
            <Row label="Avg fill" value={formatCurrency(data.average_fill_price)} />
            <Row label="Broker order" value={data.broker_order_id ?? '—'} />
            <Row label="Updated" value={formatDateTime(data.updated_at)} />
          </dl>
        )}
      </CardContent>
    </Card>
  )
}

function Row({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between">
      <dt className="text-text-secondary">{label}</dt>
      <dd className="font-medium text-text-primary">{value}</dd>
    </div>
  )
}
