import { LayersIcon } from 'lucide-react'
import { useState } from 'react'
import { useBestOptions } from '@/api/queries/options'
import type { RankedOptionResponse } from '@/api/types/options'
import { Button } from '@/components/ui/Button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { EmptyState, ErrorState } from '@/components/ui/EmptyState'
import { Input } from '@/components/ui/Input'
import { Skeleton } from '@/components/ui/Skeleton'
import { cn } from '@/lib/cn'
import { formatCurrency, formatInteger, formatNumber } from '@/lib/format'

export function OptionsPage() {
  const [input, setInput] = useState('')
  const [symbol, setSymbol] = useState<string | undefined>()
  const { data, isLoading, isError, error } = useBestOptions(symbol)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-lg font-semibold text-text-primary">Options</h1>
        <p className="text-sm text-text-secondary">Best-ranked call and put contracts for a symbol.</p>
      </div>

      <Card>
        <CardContent className="pt-4">
          <form
            className="flex gap-2"
            onSubmit={(e) => {
              e.preventDefault()
              setSymbol(input.trim().toUpperCase() || undefined)
            }}
          >
            <Input value={input} onChange={(e) => setInput(e.target.value)} placeholder="Symbol, e.g. AAPL" className="max-w-xs" />
            <Button type="submit">Find best options</Button>
          </form>
        </CardContent>
      </Card>

      {isLoading && (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <Skeleton className="h-64 w-full" />
          <Skeleton className="h-64 w-full" />
        </div>
      )}
      {isError && <ErrorState message={(error as Error).message} />}
      {!symbol && !isLoading && (
        <EmptyState icon={LayersIcon} title="Search a symbol" description="Enter a ticker above to see its best-ranked option contracts." />
      )}
      {data && (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <OptionCard label="Best call" option={data.best_call} tone="good" />
          <OptionCard label="Best put" option={data.best_put} tone="critical" />
        </div>
      )}
    </div>
  )
}

function OptionCard({ label, option, tone }: { label: string; option: RankedOptionResponse | null; tone: 'good' | 'critical' }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{label}</CardTitle>
        {option && <span className={cn('tabular-nums text-sm font-semibold', tone === 'good' ? 'text-success-text' : 'text-status-critical')}>score {option.score.toFixed(1)}</span>}
      </CardHeader>
      <CardContent>
        {!option ? (
          <p className="text-sm text-text-secondary">No {label.toLowerCase()} contract available.</p>
        ) : (
          <div className="space-y-3 text-sm">
            <p className="font-mono text-xs text-text-secondary">{option.symbol}</p>
            <div className="grid grid-cols-3 gap-2 tabular-nums">
              <Metric label="Strike" value={formatCurrency(option.strike)} />
              <Metric label="Expiry" value={option.expiry} />
              <Metric label="Last" value={formatCurrency(option.last)} />
              <Metric label="Bid" value={formatCurrency(option.bid)} />
              <Metric label="Ask" value={formatCurrency(option.ask)} />
              <Metric label="IV" value={formatNumber(option.implied_volatility, 3)} />
              <Metric label="Delta" value={formatNumber(option.delta, 3)} />
              <Metric label="Volume" value={formatInteger(option.volume)} />
              <Metric label="OI" value={formatInteger(option.open_interest)} />
            </div>
            {option.reasons.length > 0 && (
              <ul className="list-inside list-disc text-text-secondary">
                {option.reasons.map((r) => (
                  <li key={r}>{r}</li>
                ))}
              </ul>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md bg-surface-2 p-2 text-center">
      <div className="text-xs text-text-muted">{label}</div>
      <div className="font-semibold text-text-primary">{value}</div>
    </div>
  )
}
