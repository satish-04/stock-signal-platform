import type { ColumnDef } from '@tanstack/react-table'
import { useMemo, useState } from 'react'
import { useSignals } from '@/api/queries/signals'
import type { SignalStatus, TradeSignalResponse } from '@/api/types/signals'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { DataTable } from '@/components/ui/DataTable'
import { EmptyState, ErrorState } from '@/components/ui/EmptyState'
import { Input, Select } from '@/components/ui/Input'
import { SkeletonRows } from '@/components/ui/Skeleton'
import { StatusBadge } from '@/components/ui/StatusBadge'
import { formatRelativeTime } from '@/lib/format'
import { SignalDetailDrawer } from './SignalDetailDrawer'
import { TechnicalSignalLookup } from './TechnicalSignalLookup'

const STATUS_OPTIONS: { value: SignalStatus | ''; label: string }[] = [
  { value: '', label: 'All statuses' },
  { value: 'actionable', label: 'Actionable' },
  { value: 'review', label: 'Review' },
  { value: 'rejected', label: 'Rejected' },
]

export function SignalsPage() {
  const [status, setStatus] = useState<SignalStatus | ''>('')
  const [symbol, setSymbol] = useState('')
  const [selected, setSelected] = useState<TradeSignalResponse | null>(null)

  const { data, isLoading, isError, error } = useSignals({
    status: status || undefined,
    symbol: symbol || undefined,
    limit: 100,
  })

  const columns = useMemo<ColumnDef<TradeSignalResponse, unknown>[]>(
    () => [
      { header: 'Symbol', accessorKey: 'symbol', cell: (c) => <span className="font-medium">{c.getValue<string>()}</span> },
      { header: 'Direction', accessorKey: 'direction', cell: (c) => <StatusBadge status={c.getValue<string>()} /> },
      { header: 'Strategy', accessorKey: 'strategy' },
      {
        header: 'Score',
        accessorKey: 'score',
        cell: (c) => <span className="tabular-nums">{c.getValue<number>().toFixed(1)}</span>,
      },
      { header: 'Status', accessorKey: 'status', cell: (c) => <StatusBadge status={c.getValue<string>()} /> },
      {
        header: 'Risk approved',
        accessorKey: 'risk_approved',
        cell: (c) => (c.getValue<boolean>() ? 'Yes' : 'No'),
      },
      {
        header: 'Created',
        accessorKey: 'created_at',
        cell: (c) => <span className="text-text-secondary">{formatRelativeTime(c.getValue<string>())}</span>,
      },
    ],
    [],
  )

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-lg font-semibold text-text-primary">Signals</h1>
        <p className="text-sm text-text-secondary">Trade signals persisted by the signal engine, filterable by status and symbol.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Signal feed</CardTitle>
          <div className="flex gap-2">
            <Input
              value={symbol}
              onChange={(e) => setSymbol(e.target.value.toUpperCase())}
              placeholder="Filter symbol"
              className="h-8 w-32"
            />
            <Select value={status} onChange={(e) => setStatus(e.target.value as SignalStatus | '')} className="h-8 w-36">
              {STATUS_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </Select>
          </div>
        </CardHeader>
        <CardContent>
          {isLoading && <SkeletonRows rows={6} />}
          {isError && <ErrorState message={(error as Error).message} />}
          {data && data.items.length === 0 && (
            <EmptyState
              title="No signals match these filters"
              description="Try clearing filters, or seed sample data via POST /api/v1/dev/seed."
            />
          )}
          {data && data.items.length > 0 && (
            <DataTable columns={columns} data={data.items} onRowClick={setSelected} getRowId={(row) => row.id} />
          )}
        </CardContent>
      </Card>

      <TechnicalSignalLookup />

      <SignalDetailDrawer signal={selected} onClose={() => setSelected(null)} />
    </div>
  )
}
