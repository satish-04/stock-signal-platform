import { useState } from 'react'
import { useAIRecommendation } from '@/api/queries/ai'
import { Button } from '@/components/ui/Button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { ErrorState } from '@/components/ui/EmptyState'
import { Input } from '@/components/ui/Input'
import { Skeleton } from '@/components/ui/Skeleton'
import { StatusBadge } from '@/components/ui/StatusBadge'
import { formatCurrency } from '@/lib/format'

export function AIRecommendationPanel() {
  const [input, setInput] = useState('')
  const [symbol, setSymbol] = useState<string | undefined>()
  const { data, isLoading, isError, error } = useAIRecommendation(symbol)

  return (
    <Card>
      <CardHeader>
        <CardTitle>AI recommendation</CardTitle>
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
          <Button type="submit">Ask</Button>
        </form>

        {isLoading && <Skeleton className="h-40 w-full" />}
        {isError && <ErrorState message={(error as Error).message} />}
        {data && (
          <div className="space-y-3 text-sm">
            <div className="flex flex-wrap items-center gap-2">
              <StatusBadge status={data.action} />
              <StatusBadge status={data.risk} />
              <span className="tabular-nums text-text-secondary">confidence {data.confidence.toFixed(0)}%</span>
            </div>
            <p className="text-text-primary">{data.summary}</p>
            <div className="grid grid-cols-2 gap-2 tabular-nums sm:grid-cols-3">
              <Metric label="Entry" value={formatCurrency(data.entry)} />
              <Metric label="Stop loss" value={formatCurrency(data.stop_loss)} />
              <Metric label="Position size" value={`${data.position_size_pct.toFixed(1)}%`} />
            </div>
            {data.targets.length > 0 && (
              <p className="text-text-secondary">Targets: {data.targets.map((t) => formatCurrency(t)).join(', ')}</p>
            )}
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              {data.pros.length > 0 && (
                <div>
                  <h4 className="mb-1 text-xs font-semibold uppercase tracking-wide text-success-text">Pros</h4>
                  <ul className="list-inside list-disc text-text-secondary">
                    {data.pros.map((p) => (
                      <li key={p}>{p}</li>
                    ))}
                  </ul>
                </div>
              )}
              {data.cons.length > 0 && (
                <div>
                  <h4 className="mb-1 text-xs font-semibold uppercase tracking-wide text-status-critical">Cons</h4>
                  <ul className="list-inside list-disc text-text-secondary">
                    {data.cons.map((c) => (
                      <li key={c}>{c}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
            <p className="text-text-secondary">{data.reasoning}</p>
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
