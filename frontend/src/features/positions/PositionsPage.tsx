import type { ColumnDef } from '@tanstack/react-table'
import { BriefcaseIcon } from 'lucide-react'
import { useMemo, useState } from 'react'
import { usePortfolioSummary, usePositions } from '@/api/queries/positions'
import type { PositionResponse, PositionStatus } from '@/api/types/positions'
import { StatTile } from '@/components/charts/StatTile'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { DataTable } from '@/components/ui/DataTable'
import { EmptyState, ErrorState } from '@/components/ui/EmptyState'
import { Button } from '@/components/ui/Button'
import { SkeletonRows } from '@/components/ui/Skeleton'
import { StatusBadge } from '@/components/ui/StatusBadge'
import { cn } from '@/lib/cn'
import { formatCurrency, formatDateTime, formatSignedCurrency } from '@/lib/format'
import { useUIStore } from '@/store/uiStore'
import { MarkPositionDrawer } from './MarkPositionDrawer'

const TABS: { value: PositionStatus | ''; label: string }[] = [
  { value: '', label: 'All' },
  { value: 'OPEN', label: 'Open' },
  { value: 'CLOSED', label: 'Closed' },
]

export function PositionsPage() {
  const accountId = useUIStore((s) => s.selectedAccountId)
  const [tab, setTab] = useState<PositionStatus | ''>('OPEN')
  const [marking, setMarking] = useState<PositionResponse | null>(null)

  const { data: summary } = usePortfolioSummary(accountId)
  const { data, isLoading, isError, error } = usePositions(accountId, tab || undefined)

  const columns = useMemo<ColumnDef<PositionResponse, unknown>[]>(
    () => [
      { header: 'Symbol', accessorKey: 'symbol', cell: (c) => <span className="font-medium">{c.getValue<string>()}</span> },
      { header: 'Option', accessorKey: 'option_symbol' },
      { header: 'Side', accessorKey: 'side', cell: (c) => <StatusBadge status={c.getValue<string>()} /> },
      { header: 'Status', accessorKey: 'status', cell: (c) => <StatusBadge status={c.getValue<string>()} /> },
      { header: 'Qty', accessorKey: 'quantity', cell: (c) => <span className="tabular-nums">{c.getValue<number>()}</span> },
      {
        header: 'Entry',
        accessorKey: 'average_entry_price',
        cell: (c) => <span className="tabular-nums">{formatCurrency(c.getValue<string>())}</span>,
      },
      {
        header: 'Mark',
        accessorKey: 'current_mark_price',
        cell: (c) => <span className="tabular-nums">{formatCurrency(c.getValue<string | null>())}</span>,
      },
      {
        header: 'Unrealized P&L',
        accessorKey: 'unrealized_pnl',
        cell: (c) => {
          const v = c.getValue<string | null>()
          return (
            <span className={cn('tabular-nums', v && Number(v) >= 0 ? 'text-success-text' : 'text-status-critical')}>
              {formatSignedCurrency(v)}
            </span>
          )
        },
      },
      { header: 'Updated', accessorKey: 'updated_at', cell: (c) => formatDateTime(c.getValue<string>()) },
      {
        header: '',
        id: 'actions',
        cell: (c) => (
          <Button
            size="sm"
            variant="secondary"
            onClick={(e) => {
              e.stopPropagation()
              setMarking(c.row.original)
            }}
          >
            Mark
          </Button>
        ),
      },
    ],
    [],
  )

  if (!accountId) {
    return (
      <div className="space-y-6">
        <h1 className="text-lg font-semibold text-text-primary">Positions</h1>
        <EmptyState
          icon={BriefcaseIcon}
          title="No account selected"
          description="Enter an account ID in the top bar to load positions and portfolio summary."
        />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-lg font-semibold text-text-primary">Positions</h1>
        <p className="text-sm text-text-secondary">Account {accountId}</p>
      </div>

      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <StatTile label="Total P&L" value={summary ? formatSignedCurrency(summary.total_pnl) : '—'} tone={summary && Number(summary.total_pnl) >= 0 ? 'good' : 'critical'} />
        <StatTile label="Realized" value={summary ? formatSignedCurrency(summary.realized_pnl) : '—'} />
        <StatTile label="Unrealized" value={summary ? formatSignedCurrency(summary.unrealized_pnl) : '—'} />
        <StatTile label="Market value" value={summary ? formatCurrency(summary.total_market_value) : '—'} />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Positions</CardTitle>
          <div className="flex gap-1 rounded-md bg-surface-2 p-0.5">
            {TABS.map((t) => (
              <button
                key={t.value}
                onClick={() => setTab(t.value)}
                className={cn(
                  'rounded px-2.5 py-1 text-xs font-medium',
                  tab === t.value ? 'bg-surface text-text-primary shadow-sm' : 'text-text-secondary',
                )}
              >
                {t.label}
              </button>
            ))}
          </div>
        </CardHeader>
        <CardContent>
          {isLoading && <SkeletonRows rows={5} />}
          {isError && <ErrorState message={(error as Error).message} />}
          {data && data.items.length === 0 && (
            <EmptyState title="No positions" description="No positions found for this account and filter." />
          )}
          {data && data.items.length > 0 && (
            <DataTable columns={columns} data={data.items} getRowId={(row) => row.position_id} stickyFirstColumn />
          )}
        </CardContent>
      </Card>

      <MarkPositionDrawer position={marking} accountId={accountId} onClose={() => setMarking(null)} />
    </div>
  )
}
