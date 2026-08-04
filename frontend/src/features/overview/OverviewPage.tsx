import { ActivityIcon, BriefcaseIcon, ServerIcon, WorkflowIcon } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useHealth, useWorkerHealth } from '@/api/queries/health'
import { usePortfolioSummary } from '@/api/queries/positions'
import { useSignals } from '@/api/queries/signals'
import { useWorkflows } from '@/api/queries/workflows'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { StatusBadge } from '@/components/ui/StatusBadge'
import { StatTile } from '@/components/charts/StatTile'
import { Skeleton } from '@/components/ui/Skeleton'
import { EmptyState } from '@/components/ui/EmptyState'
import { formatCurrency, formatRelativeTime } from '@/lib/format'
import { useUIStore } from '@/store/uiStore'

export function OverviewPage() {
  const accountId = useUIStore((s) => s.selectedAccountId)
  const { data: health } = useHealth()
  const { data: workerHealth } = useWorkerHealth()
  const { data: portfolio } = usePortfolioSummary(accountId)
  const { data: signals } = useSignals({ status: 'actionable', limit: 8 })
  const { data: workflows } = useWorkflows(accountId)

  const activeWorkflows = workflows?.filter((w) => !['COMPLETED', 'FAILED', 'CANCELLED'].includes(w.status)) ?? []

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-lg font-semibold text-text-primary">Overview</h1>
        <p className="text-sm text-text-secondary">Command center for signals, portfolio, and automation health.</p>
      </div>

      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <StatTile
          label="Portfolio P&L"
          value={portfolio ? formatCurrency(portfolio.total_pnl) : '—'}
          icon={BriefcaseIcon}
          tone={portfolio && Number(portfolio.total_pnl) >= 0 ? 'good' : 'critical'}
          hint={portfolio ? `${portfolio.open_positions} open · ${portfolio.closed_positions} closed` : accountId ? 'Loading…' : 'Set an account ID'}
        />
        <StatTile
          label="Actionable Signals"
          value={signals ? String(signals.count) : '—'}
          icon={ActivityIcon}
          hint="last 5s poll"
        />
        <StatTile
          label="Active Workflows"
          value={accountId ? String(activeWorkflows.length) : '—'}
          icon={WorkflowIcon}
          hint={accountId ? undefined : 'Set an account ID'}
        />
        <StatTile
          label="Worker"
          value={workerHealth ? (workerHealth.status === 'ok' ? 'Healthy' : 'Degraded') : '—'}
          icon={ServerIcon}
          tone={workerHealth ? (workerHealth.status === 'ok' ? 'good' : 'critical') : 'neutral'}
          hint={workerHealth ? workerHealth.queue_name : undefined}
        />
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Platform status</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            {!health ? (
              <Skeleton className="h-24 w-full" />
            ) : (
              <>
                <Row label="API" value={<StatusBadge status={health.status} />} />
                <Row label="Environment" value={health.environment} />
                <Row label="Trading mode" value={health.trading_mode} />
                <Row label="Market data" value={health.market_data_mode} />
                <Row label="Order submission" value={health.orders_enabled ? 'Enabled' : 'Disabled'} />
              </>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Recent actionable signals</CardTitle>
            <Link to="/signals" className="text-xs font-medium text-series-1 hover:underline">
              View all
            </Link>
          </CardHeader>
          <CardContent>
            {!signals ? (
              <Skeleton className="h-24 w-full" />
            ) : signals.items.length === 0 ? (
              <EmptyState title="No actionable signals yet" description="Seed data or wait for TradingView webhooks to arrive." />
            ) : (
              <ul className="divide-y divide-border">
                {signals.items.map((s) => (
                  <li key={s.id} className="flex items-center justify-between py-2 text-sm">
                    <div>
                      <span className="font-medium text-text-primary">{s.symbol}</span>
                      <span className="ml-2 text-text-secondary">{s.strategy}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="tabular-nums text-text-secondary">{s.score.toFixed(0)}</span>
                      <span className="text-xs text-text-muted">{formatRelativeTime(s.created_at)}</span>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

function Row({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-text-secondary">{label}</span>
      <span className="font-medium text-text-primary">{value}</span>
    </div>
  )
}
