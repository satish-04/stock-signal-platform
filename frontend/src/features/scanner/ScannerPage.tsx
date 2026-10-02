import type { ColumnDef } from '@tanstack/react-table'
import { RadarIcon } from 'lucide-react'
import { useMemo, useState } from 'react'
import { useLatestOptionsScan, useOptionsScanProgress, useStartOptionsScan } from '@/api/queries/scanner'
import type { ScanItem, ScanStrike } from '@/api/types/scanner'
import { Button } from '@/components/ui/Button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { DataTable } from '@/components/ui/DataTable'
import { EmptyState, ErrorState } from '@/components/ui/EmptyState'
import { Input, Label } from '@/components/ui/Input'
import { SkeletonRows } from '@/components/ui/Skeleton'
import { cn } from '@/lib/cn'
import { formatCompact, formatDateTime, formatNumber, formatPercent } from '@/lib/format'
import { formatExpiry, formatIv } from './format'
import { StrikeDetailDrawer } from './StrikeDetailDrawer'

type Ranking = 'volume' | 'iv'

const ROWS = 25

export function ScannerPage() {
  const [expiry, setExpiry] = useState('')
  const [ranking, setRanking] = useState<Ranking>('volume')
  const [selected, setSelected] = useState<ScanItem | null>(null)

  const latest = useLatestOptionsScan()
  const start = useStartOptionsScan()
  const scan = latest.data?.scan ?? null
  const runningId = scan?.status === 'running' ? scan.id : undefined
  const polled = useOptionsScanProgress(runningId)
  const progress = polled.data?.scan.progress ?? scan?.progress ?? null
  const running = !!runningId || start.isPending

  // Results stay on screen while a newer scan runs or after one fails.
  const shown = scan?.status === 'completed' ? scan : (latest.data?.last_completed ?? null)
  const result = shown?.result ?? null

  const rows = useMemo(() => {
    if (!result) return []
    if (ranking === 'volume') return result.items.slice(0, ROWS)
    const bySymbol = new Map(result.items.map((item) => [item.symbol, item]))
    return result.top_iv.flatMap((symbol) => bySymbol.get(symbol) ?? [])
  }, [result, ranking])

  const columns = useMemo<ColumnDef<ScanItem, unknown>[]>(
    () => [
      { header: 'Symbol', accessorKey: 'symbol', cell: (c) => <span className="font-medium">{c.getValue<string>()}</span> },
      { header: 'Last', accessorKey: 'spot', cell: (c) => <span className="tabular-nums">{formatNumber(c.getValue<number>())}</span> },
      {
        header: 'Change',
        accessorKey: 'change_pct',
        cell: (c) => {
          const value = c.getValue<number>()
          return (
            <span className={cn('tabular-nums', value < 0 ? 'text-status-critical' : 'text-success-text')}>
              {value > 0 ? '+' : ''}
              {formatPercent(value, 2)}
            </span>
          )
        },
      },
      {
        header: 'Contracts',
        accessorKey: 'total_volume',
        cell: (c) => <span className="tabular-nums">{formatCompact(c.getValue<number>())}</span>,
      },
      {
        header: 'Put/call',
        accessorKey: 'put_call_ratio',
        cell: (c) => <span className="tabular-nums">{formatNumber(c.getValue<number | null>())}</span>,
      },
      {
        header: 'ATM IV',
        accessorKey: 'atm_iv',
        cell: (c) => <span className="tabular-nums">{formatIv(c.getValue<number | null>())}</span>,
      },
      {
        header: 'Implied move',
        accessorKey: 'implied_move_pct',
        cell: (c) => <span className="tabular-nums">±{formatPercent(c.getValue<number>())}</span>,
      },
      {
        id: 'top_call',
        header: 'Top call strike',
        enableSorting: false,
        cell: (c) => <TopStrike strike={c.row.original.top_calls[0]} />,
      },
      {
        id: 'top_put',
        header: 'Top put strike',
        enableSorting: false,
        cell: (c) => <TopStrike strike={c.row.original.top_puts[0]} />,
      },
    ],
    [],
  )

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-lg font-semibold text-text-primary">Options scanner</h1>
        <p className="text-sm text-text-secondary">
          Where options volume and implied volatility are concentrated, scanned on demand.
        </p>
      </div>

      <Card>
        <CardContent className="space-y-3 pt-4">
          <form
            className="flex flex-wrap items-end gap-3"
            onSubmit={(e) => {
              e.preventDefault()
              start.mutate(expiry ? { expiry } : {})
            }}
          >
            <div>
              <Label htmlFor="scanner-expiry">Expiry (optional)</Label>
              <Input
                id="scanner-expiry"
                type="date"
                value={expiry}
                onChange={(e) => setExpiry(e.target.value)}
                className="w-44"
              />
            </div>
            <Button type="submit" disabled={running}>
              <RadarIcon className="h-4 w-4" aria-hidden="true" />
              {running ? 'Scanning…' : 'Scan market'}
            </Button>
            <p className="pb-2 text-xs text-text-muted">Leave the date empty to scan the next weekly expiry.</p>
          </form>

          {start.isError && <p className="text-sm text-status-critical">{(start.error as Error).message}</p>}
          {scan?.status === 'failed' && !running && (
            <p className="text-sm text-status-critical">Last scan failed: {scan.error}</p>
          )}
          {running && (
            <div className="flex items-center gap-3 text-sm text-text-secondary" role="status">
              <div className="h-1.5 w-56 max-w-full overflow-hidden rounded-full bg-hover">
                <div
                  className="h-full rounded-full bg-series-1 transition-all duration-500"
                  style={{ width: `${progress?.total ? (progress.done / progress.total) * 100 : 0}%` }}
                />
              </div>
              <span className="tabular-nums">
                {progress?.total ? `Scanned ${progress.done} of ${progress.total} symbols` : 'Building the symbol list…'}
              </span>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex-wrap">
          <CardTitle>
            {shown ? `${formatExpiry(shown.expiry)} expiry · ${shown.scanned} symbols` : 'Scan results'}
          </CardTitle>
          {result && (
            <div className="flex gap-1" role="tablist" aria-label="Ranking">
              <Button
                size="sm"
                role="tab"
                aria-selected={ranking === 'volume'}
                variant={ranking === 'volume' ? 'secondary' : 'ghost'}
                onClick={() => setRanking('volume')}
              >
                Highest volume
              </Button>
              <Button
                size="sm"
                role="tab"
                aria-selected={ranking === 'iv'}
                variant={ranking === 'iv' ? 'secondary' : 'ghost'}
                onClick={() => setRanking('iv')}
              >
                Highest IV
              </Button>
            </div>
          )}
        </CardHeader>
        <CardContent className="space-y-3">
          {latest.isLoading && <SkeletonRows rows={6} />}
          {latest.isError && <ErrorState message={(latest.error as Error).message} />}
          {latest.data && !result && (
            <EmptyState
              icon={RadarIcon}
              title="No scan results yet"
              description="Run a scan to see where options activity is concentrated."
            />
          )}
          {shown && result && (
            <>
              {rows.length > 0 ? (
                <DataTable columns={columns} data={rows} onRowClick={setSelected} getRowId={(row) => row.symbol} />
              ) : (
                <EmptyState title="No symbols had a chain for this expiry" />
              )}
              <p className="text-xs text-text-muted">
                {ranking === 'volume'
                  ? 'Ranked by contracts traded for this expiry.'
                  : `Symbols with at least ${formatCompact(result.iv_min_volume)} contracts traded, ranked by at-the-money implied volatility.`}{' '}
                Quotes as of {formatDateTime(result.quotes_as_of)}, scanned {formatDateTime(shown.completed_at)}. Select
                a row for its most-traded strikes. Yahoo Finance data; scans are research only and never create signals
                or orders.
              </p>
              {result.skipped.length > 0 && (
                <details className="text-xs text-text-secondary">
                  <summary className="cursor-pointer font-medium">{result.skipped.length} symbols skipped</summary>
                  <p className="mt-1 break-words">
                    {result.skipped
                      .map((entry) => (entry.reason.startsWith('error') ? `${entry.symbol} (${entry.reason})` : entry.symbol))
                      .join(', ')}
                  </p>
                </details>
              )}
            </>
          )}
        </CardContent>
      </Card>

      <StrikeDetailDrawer item={selected} onClose={() => setSelected(null)} />
    </div>
  )
}

function TopStrike({ strike }: { strike: ScanStrike | undefined }) {
  if (!strike) return <>—</>
  return (
    <span className="tabular-nums">
      {strike.strike} <span className="text-text-muted">· {formatCompact(strike.volume)}</span>
    </span>
  )
}
