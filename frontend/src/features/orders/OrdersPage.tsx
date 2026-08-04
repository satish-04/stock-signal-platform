import { ListChecksIcon } from 'lucide-react'
import { useHealth } from '@/api/queries/health'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { EmptyState } from '@/components/ui/EmptyState'
import { useOrdersStore } from '@/store/ordersStore'
import { ExecutionLookup } from './ExecutionLookup'
import { OrderRow } from './OrderRow'

export function OrdersPage() {
  const entries = useOrdersStore((s) => s.entries)
  const { data: health } = useHealth()

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-lg font-semibold text-text-primary">Orders</h1>
        <p className="text-sm text-text-secondary">
          Order intents sent from this browser session, plus lookup for any execution by ID. The backend has no
          list endpoint, so this blotter reflects local session history only.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Session order blotter</CardTitle>
        </CardHeader>
        <CardContent>
          {entries.length === 0 ? (
            <EmptyState
              icon={ListChecksIcon}
              title="No orders yet"
              description="Build and approve a trade plan on the Risk & AI page to send it here."
            />
          ) : (
            <div className="scroll-thin overflow-x-auto">
              <table className="w-full border-collapse text-sm">
                <thead>
                  <tr className="border-b border-border text-left text-xs font-medium uppercase tracking-wide text-text-muted">
                    <th className="px-3 py-2">Symbol</th>
                    <th className="px-3 py-2">Option</th>
                    <th className="px-3 py-2">Side</th>
                    <th className="px-3 py-2">Qty</th>
                    <th className="px-3 py-2">Status</th>
                    <th className="px-3 py-2">Avg fill</th>
                    <th className="px-3 py-2">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {entries.map((entry) => (
                    <OrderRow key={entry.intentId} entry={entry} ordersEnabled={health?.orders_enabled ?? false} />
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      <ExecutionLookup />
    </div>
  )
}
