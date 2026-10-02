import { FlaskConicalIcon } from 'lucide-react'
import { useState } from 'react'
import { useBacktest, useMarketRegime } from '@/api/queries/quant'
import type { BacktestMetrics, BacktestResponse, BacktestStrategy } from '@/api/types/quant'
import { StatTile } from '@/components/charts/StatTile'
import { Button } from '@/components/ui/Button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { EmptyState } from '@/components/ui/EmptyState'
import { Input, Label, Select } from '@/components/ui/Input'
import { Skeleton } from '@/components/ui/Skeleton'
import { formatNumber, formatPercent } from '@/lib/format'
import { EquityCurve } from './EquityCurve'

const STRATEGIES: { value: BacktestStrategy; label: string }[] = [
  { value: 'ema_cross', label: 'EMA crossover (trend)' },
  { value: 'rsi_reversion', label: 'RSI mean reversion' },
]

const paramText = (params: Record<string, number>) =>
  Object.entries(params)
    .map(([key, value]) => `${key} ${value}`)
    .join(' · ')

export function QuantPage() {
  const [symbol, setSymbol] = useState('SPY')
  const [strategy, setStrategy] = useState<BacktestStrategy>('ema_cross')
  const [years, setYears] = useState(5)
  const backtest = useBacktest()
  const result = backtest.data

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-lg font-semibold text-text-primary">Quant lab</h1>
        <p className="text-sm text-text-secondary">
          Test a strategy on daily history, see how it holds up on unseen data, and read the current market regime.
        </p>
      </div>

      <RegimeCard />

      <Card>
        <CardHeader>
          <CardTitle>Backtest</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <form
            className="flex flex-wrap items-end gap-3"
            onSubmit={(e) => {
              e.preventDefault()
              backtest.mutate({ symbol: symbol.trim().toUpperCase(), strategy, years, cost_bps: 5 })
            }}
          >
            <div>
              <Label htmlFor="quant-symbol">Symbol</Label>
              <Input
                id="quant-symbol"
                value={symbol}
                onChange={(e) => setSymbol(e.target.value.toUpperCase())}
                maxLength={16}
                className="w-28"
              />
            </div>
            <div>
              <Label htmlFor="quant-strategy">Strategy</Label>
              <Select
                id="quant-strategy"
                value={strategy}
                onChange={(e) => setStrategy(e.target.value as BacktestStrategy)}
                className="w-56"
              >
                {STRATEGIES.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </Select>
            </div>
            <div>
              <Label htmlFor="quant-years">History</Label>
              <Select id="quant-years" value={years} onChange={(e) => setYears(Number(e.target.value))} className="w-28">
                {[3, 5, 10].map((value) => (
                  <option key={value} value={value}>
                    {value} years
                  </option>
                ))}
              </Select>
            </div>
            <Button type="submit" disabled={backtest.isPending || !symbol.trim()}>
              <FlaskConicalIcon className="h-4 w-4" aria-hidden="true" />
              {backtest.isPending ? 'Running…' : 'Run backtest'}
            </Button>
          </form>
          {backtest.isError && <p className="text-sm text-status-critical">{(backtest.error as Error).message}</p>}
        </CardContent>
      </Card>

      {backtest.isPending && <Skeleton className="h-64 w-full" />}
      {!result && !backtest.isPending && (
        <EmptyState
          icon={FlaskConicalIcon}
          title="No backtest yet"
          description="Run one to sweep the strategy's parameters and validate the result walk-forward."
        />
      )}
      {result && !backtest.isPending && <BacktestResult result={result} />}
    </div>
  )
}

function RegimeCard() {
  const { data, isLoading, isError } = useMarketRegime()
  return (
    <Card>
      <CardHeader>
        <CardTitle>Market regime{data ? ` · ${data.symbol}` : ''}</CardTitle>
        {data && <span className="text-xs text-text-secondary">as of {data.as_of}</span>}
      </CardHeader>
      <CardContent>
        {isLoading && <Skeleton className="h-16 w-full" />}
        {isError && <p className="text-sm text-text-secondary">Regime data is unavailable right now.</p>}
        {data && (
          <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
            <StatTile
              label="Trend"
              value={data.trend === 'up' ? 'Up' : data.trend === 'down' ? 'Down' : 'Mixed'}
              tone={data.trend === 'up' ? 'good' : data.trend === 'down' ? 'critical' : 'neutral'}
              hint={`Close ${formatNumber(data.close)} vs 200-day average ${formatNumber(data.sma200)}`}
            />
            <StatTile
              label="Volatility"
              value={data.volatility === 'high' ? 'High' : 'Normal'}
              tone={data.volatility === 'high' ? 'critical' : 'neutral'}
              hint={`${formatPercent(data.realized_vol_pct)} annualised, higher than ${data.vol_percentile}% of the past year`}
            />
            <StatTile label="Bullish trades" value={`${data.scores.bullish} / 100`} hint="Regime support for a bullish signal" />
            <StatTile label="Bearish trades" value={`${data.scores.bearish} / 100`} hint="Regime support for a bearish signal" />
          </div>
        )}
      </CardContent>
    </Card>
  )
}

function BacktestResult({ result }: { result: BacktestResponse }) {
  const walk = result.walk_forward
  return (
    <>
      <Card>
        <CardHeader className="flex-wrap">
          <CardTitle>
            {result.symbol} · best of {result.combinations} parameter sets · {paramText(result.best.params)}
          </CardTitle>
          <span className="text-xs text-text-secondary">
            {result.start} to {result.end}
          </span>
        </CardHeader>
        <CardContent className="space-y-4">
          <EquityCurve curve={result.equity_curve} />
          <MetricsTable
            rows={[
              { label: 'Strategy (best parameters)', metrics: result.best },
              { label: 'Buy and hold', metrics: result.benchmark },
              ...(walk ? [{ label: 'Walk-forward, unseen data only', metrics: walk.out_of_sample }] : []),
            ]}
          />
          <p className="text-xs text-text-muted">
            The best parameters were picked with hindsight on this same history, so that row flatters the strategy.
            The walk-forward row only trades parameters chosen on earlier data. Costs of {result.cost_bps} basis
            points per position change are included. Daily bars, long or flat, no leverage.
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Walk-forward validation</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {!walk ? (
            <p className="text-sm text-text-secondary">
              Not enough history for a training and a test window. Choose a longer history.
            </p>
          ) : (
            <>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
                <StatTile label="Sharpe while fitting" value={formatNumber(walk.average_in_sample_sharpe)} hint="Average across training windows" />
                <StatTile
                  label="Sharpe on unseen data"
                  value={formatNumber(walk.out_of_sample.sharpe)}
                  tone={walk.out_of_sample.sharpe > 0 ? 'good' : 'critical'}
                  hint={`${walk.windows.length} test windows of ${walk.test_days} trading days`}
                />
                <StatTile
                  label="Edge retained"
                  value={walk.sharpe_retained_pct === null ? '—' : formatPercent(walk.sharpe_retained_pct, 0)}
                  hint="Near zero or negative means the sweep fitted noise"
                />
              </div>
              <div className="scroll-thin overflow-x-auto">
                <table className="w-full border-collapse text-sm tabular-nums">
                  <thead>
                    <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-text-muted">
                      <th className="px-3 py-2 font-medium">Test window</th>
                      <th className="px-3 py-2 font-medium">Parameters chosen beforehand</th>
                      <th className="px-3 py-2 font-medium">Sharpe while fitting</th>
                      <th className="px-3 py-2 font-medium">Sharpe on unseen data</th>
                    </tr>
                  </thead>
                  <tbody>
                    {walk.windows.map((window) => (
                      <tr key={window.test_start} className="border-b border-border last:border-0">
                        <td className="whitespace-nowrap px-3 py-2">
                          {window.test_start} to {window.test_end}
                        </td>
                        <td className="whitespace-nowrap px-3 py-2">{paramText(window.params)}</td>
                        <td className="px-3 py-2">{formatNumber(window.in_sample_sharpe)}</td>
                        <td className={`px-3 py-2 ${window.out_of_sample_sharpe < 0 ? 'text-status-critical' : ''}`}>
                          {formatNumber(window.out_of_sample_sharpe)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </>
  )
}

function MetricsTable({ rows }: { rows: { label: string; metrics: BacktestMetrics }[] }) {
  return (
    <div className="scroll-thin overflow-x-auto">
      <table className="w-full border-collapse text-sm tabular-nums">
        <thead>
          <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-text-muted">
            <th className="px-3 py-2 font-medium" />
            <th className="px-3 py-2 font-medium">Return</th>
            <th className="px-3 py-2 font-medium">Per year</th>
            <th className="px-3 py-2 font-medium">Sharpe</th>
            <th className="px-3 py-2 font-medium">Worst drawdown</th>
            <th className="px-3 py-2 font-medium">Trades</th>
            <th className="px-3 py-2 font-medium">Win rate</th>
            <th className="px-3 py-2 font-medium">Time invested</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(({ label, metrics }) => (
            <tr key={label} className="border-b border-border last:border-0">
              <td className="whitespace-nowrap px-3 py-2 font-medium text-text-primary">{label}</td>
              <td className="px-3 py-2">{formatPercent(metrics.total_return_pct)}</td>
              <td className="px-3 py-2">{formatPercent(metrics.cagr_pct)}</td>
              <td className="px-3 py-2">{formatNumber(metrics.sharpe)}</td>
              <td className="px-3 py-2">{formatPercent(metrics.max_drawdown_pct)}</td>
              <td className="px-3 py-2">{metrics.trades}</td>
              <td className="px-3 py-2">{formatPercent(metrics.win_rate_pct)}</td>
              <td className="px-3 py-2">{formatPercent(metrics.exposure_pct, 0)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
