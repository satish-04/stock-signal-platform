import { toast } from 'sonner'
import { useCreateExecutionFromIntent, useCancelExecution, useExecution, useSubmitExecution } from '@/api/queries/orderExecutions'
import { Button } from '@/components/ui/Button'
import { StatusBadge } from '@/components/ui/StatusBadge'
import { formatCurrency } from '@/lib/format'
import { TERMINAL_EXECUTION_STATUSES } from '@/api/types/orderExecutions'
import type { OrderBlotterEntry } from '@/store/ordersStore'
import { useOrdersStore } from '@/store/ordersStore'

export function OrderRow({ entry, ordersEnabled }: { entry: OrderBlotterEntry; ordersEnabled: boolean }) {
  const linkExecution = useOrdersStore((s) => s.linkExecution)
  const createExecution = useCreateExecutionFromIntent()
  const execution = useExecution(entry.executionId)
  const submitExecution = useSubmitExecution()
  const cancelExecution = useCancelExecution()

  const status = execution.data?.status
  const isTerminal = status ? TERMINAL_EXECUTION_STATUSES.includes(status) : false

  return (
    <tr className="border-b border-border last:border-0">
      <td className="px-3 py-2 font-medium text-text-primary">{entry.symbol}</td>
      <td className="px-3 py-2 text-text-secondary">{entry.optionSymbol}</td>
      <td className="px-3 py-2">{entry.side}</td>
      <td className="px-3 py-2 tabular-nums">{entry.quantity}</td>
      <td className="px-3 py-2">
        {execution.data ? (
          <StatusBadge status={execution.data.status} />
        ) : entry.executionId ? (
          <span className="text-text-muted">loading…</span>
        ) : (
          <span className="text-text-muted">no execution</span>
        )}
      </td>
      <td className="px-3 py-2 tabular-nums">{formatCurrency(execution.data?.average_fill_price ?? null)}</td>
      <td className="px-3 py-2">
        <div className="flex gap-1.5">
          {!entry.executionId && (
            <Button
              size="sm"
              variant="secondary"
              disabled={createExecution.isPending}
              onClick={() =>
                createExecution.mutate(entry.intentId, {
                  onSuccess: (exec) => {
                    linkExecution(entry.intentId, exec.execution_id)
                    toast.success('Execution created')
                  },
                  onError: (err) => toast.error(err instanceof Error ? err.message : 'Failed to create execution'),
                })
              }
            >
              Create execution
            </Button>
          )}
          {entry.executionId && status === 'CREATED' && (
            <Button
              size="sm"
              variant="secondary"
              disabled={!ordersEnabled || submitExecution.isPending}
              title={ordersEnabled ? undefined : 'Order submission disabled (ENABLE_ORDER_SUBMISSION=false)'}
              onClick={() =>
                submitExecution.mutate(entry.executionId!, {
                  onError: (err) => toast.error(err instanceof Error ? err.message : 'Submit failed'),
                })
              }
            >
              Submit
            </Button>
          )}
          {entry.executionId && !isTerminal && status && status !== 'CREATED' && (
            <Button
              size="sm"
              variant="danger"
              disabled={cancelExecution.isPending}
              onClick={() =>
                cancelExecution.mutate(entry.executionId!, {
                  onError: (err) => toast.error(err instanceof Error ? err.message : 'Cancel failed'),
                })
              }
            >
              Cancel
            </Button>
          )}
        </div>
      </td>
    </tr>
  )
}
