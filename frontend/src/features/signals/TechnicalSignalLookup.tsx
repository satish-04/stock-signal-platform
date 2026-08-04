import { useState } from 'react'
import { useTechnicalSignal } from '@/api/queries/signals'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { StatusBadge } from '@/components/ui/StatusBadge'
import { Skeleton } from '@/components/ui/Skeleton'
import { ErrorState } from '@/components/ui/EmptyState'

export function TechnicalSignalLookup() {
  const [input, setInput] = useState('')
  const [symbol, setSymbol] = useState<string | undefined>()
  const { data, isLoading, isError, error } = useTechnicalSignal(symbol)

  return (
    <Card>
      <CardHeader>
        <CardTitle>Technical signal lookup</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <form
          className="flex gap-2"
          onSubmit={(e) => {
            e.preventDefault()
            setSymbol(input.trim().toUpperCase() || undefined)
          }}
        >
          <Input value={input} onChange={(e) => setInput(e.target.value)} placeholder="Symbol, e.g. AAPL" />
          <Button type="submit" size="md">
            Lookup
          </Button>
        </form>

        {isLoading && <Skeleton className="h-32 w-full" />}
        {isError && <ErrorState message={(error as Error).message} />}
        {data && (
          <div className="space-y-2 text-sm">
            <div className="flex items-center gap-2">
              <StatusBadge status={data.direction} />
              <span className="tabular-nums text-text-secondary">confidence {data.confidence.toFixed(0)}%</span>
            </div>
            <div className="grid grid-cols-2 gap-2 tabular-nums text-xs sm:grid-cols-4">
              <ScoreCell label="Trend" value={data.trend_score} />
              <ScoreCell label="Momentum" value={data.momentum_score} />
              <ScoreCell label="Volatility" value={data.volatility_score} />
              <ScoreCell label="Volume" value={data.volume_score} />
            </div>
            {data.reasons.length > 0 && (
              <ul className="list-inside list-disc text-text-secondary">
                {data.reasons.map((r) => (
                  <li key={r}>{r}</li>
                ))}
              </ul>
            )}
            {data.warnings.length > 0 && (
              <ul className="list-inside list-disc text-status-warning">
                {data.warnings.map((w) => (
                  <li key={w}>{w}</li>
                ))}
              </ul>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

function ScoreCell({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-md bg-surface-2 p-2 text-center">
      <div className="text-text-muted">{label}</div>
      <div className="font-semibold text-text-primary">{value.toFixed(0)}</div>
    </div>
  )
}
