import { CandlestickChartIcon } from 'lucide-react'
import { useMemo, useState } from 'react'
import type { UTCTimestamp } from 'lightweight-charts'
import { useHistoricalBars, useTechnicalAnalysis } from '@/api/queries/historical'
import type { TechnicalAnalysisResponse } from '@/api/types/analysis'
import { Button } from '@/components/ui/Button'
import { PriceChart, type PriceLevel } from '@/components/charts/PriceChart'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { EmptyState, ErrorState } from '@/components/ui/EmptyState'
import { Input, Select } from '@/components/ui/Input'
import { Skeleton } from '@/components/ui/Skeleton'
import { formatNumber } from '@/lib/format'

const DURATIONS = ['1 D', '5 D', '1 M']
const BAR_SIZES = ['1 min', '5 mins', '15 mins', '1 hour']

type LevelKey = keyof Pick<TechnicalAnalysisResponse, 'ema_9' | 'ema_20' | 'ema_50' | 'vwap' | 'bollinger_upper' | 'bollinger_lower'>

const LEVEL_SPECS: { key: LevelKey; label: string; color: string }[] = [
  { key: 'ema_9', label: 'EMA 9', color: 'var(--series-1)' },
  { key: 'ema_20', label: 'EMA 20', color: 'var(--series-2)' },
  { key: 'ema_50', label: 'EMA 50', color: 'var(--series-3)' },
  { key: 'vwap', label: 'VWAP', color: 'var(--series-7)' },
  { key: 'bollinger_upper', label: 'BB Upper', color: 'var(--baseline)' },
  { key: 'bollinger_lower', label: 'BB Lower', color: 'var(--baseline)' },
]

export function MarketPage() {
  const [input, setInput] = useState('')
  const [symbol, setSymbol] = useState<string | undefined>()
  const [duration, setDuration] = useState('5 D')
  const [barSize, setBarSize] = useState('5 mins')

  const params = { duration, bar_size: barSize, use_rth: true }
  const bars = useHistoricalBars(symbol, params)
  const analysis = useTechnicalAnalysis(symbol, params)

  const candles = useMemo(
    () =>
      bars.data?.bars.map((b) => ({
        time: Math.floor(new Date(b.timestamp).getTime() / 1000) as UTCTimestamp,
        open: Number(b.open),
        high: Number(b.high),
        low: Number(b.low),
        close: Number(b.close),
      })) ?? [],
    [bars.data],
  )

  const levels = useMemo<PriceLevel[]>(() => {
    if (!analysis.data) return []
    return LEVEL_SPECS.filter((spec) => analysis.data![spec.key] !== null).map((spec) => ({
      price: analysis.data![spec.key] as number,
      color: spec.color,
      title: spec.label,
    }))
  }, [analysis.data])

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-lg font-semibold text-text-primary">Market</h1>
        <p className="text-sm text-text-secondary">Historical price action with current indicator levels overlaid.</p>
      </div>

      <Card>
        <CardContent className="flex flex-wrap items-end gap-2 pt-4">
          <form
            className="flex gap-2"
            onSubmit={(e) => {
              e.preventDefault()
              setSymbol(input.trim().toUpperCase() || undefined)
            }}
          >
            <Input value={input} onChange={(e) => setInput(e.target.value)} placeholder="Symbol, e.g. AAPL" className="w-40" />
            <Button type="submit">Load</Button>
          </form>
          <Select value={duration} onChange={(e) => setDuration(e.target.value)} className="w-28">
            {DURATIONS.map((d) => (
              <option key={d} value={d}>
                {d}
              </option>
            ))}
          </Select>
          <Select value={barSize} onChange={(e) => setBarSize(e.target.value)} className="w-32">
            {BAR_SIZES.map((b) => (
              <option key={b} value={b}>
                {b}
              </option>
            ))}
          </Select>
        </CardContent>
      </Card>

      {!symbol && (
        <EmptyState icon={CandlestickChartIcon} title="Search a symbol" description="Enter a ticker above to load its chart." />
      )}

      {symbol && (
        <Card>
          <CardHeader>
            <CardTitle>{symbol}</CardTitle>
          </CardHeader>
          <CardContent>
            {bars.isLoading && <Skeleton className="h-96 w-full" />}
            {bars.isError && <ErrorState message={(bars.error as Error).message} />}
            {bars.data && bars.data.bars.length === 0 && (
              <EmptyState title="No bars returned" description="Try a different duration or bar size." />
            )}
            {candles.length > 0 && <PriceChart candles={candles} levels={levels} />}
          </CardContent>
        </Card>
      )}

      {symbol && analysis.data && (
        <Card>
          <CardHeader>
            <CardTitle>Indicators</CardTitle>
          </CardHeader>
          <CardContent className="grid grid-cols-2 gap-2 sm:grid-cols-4 lg:grid-cols-6">
            <IndicatorCell label="RSI 14" value={analysis.data.rsi_14} />
            <IndicatorCell label="MACD" value={analysis.data.macd} />
            <IndicatorCell label="MACD signal" value={analysis.data.macd_signal} />
            <IndicatorCell label="MACD hist" value={analysis.data.macd_histogram} />
            <IndicatorCell label="ATR 14" value={analysis.data.atr_14} />
            <IndicatorCell label="SMA 20" value={analysis.data.sma_20} />
            <IndicatorCell label="EMA 200" value={analysis.data.ema_200} />
            <IndicatorCell label="BB Mid" value={analysis.data.bollinger_middle} />
          </CardContent>
        </Card>
      )}
    </div>
  )
}

function IndicatorCell({ label, value }: { label: string; value: number | null }) {
  return (
    <div className="rounded-md bg-surface-2 p-2 text-center">
      <div className="text-xs text-text-muted">{label}</div>
      <div className="tabular-nums font-semibold text-text-primary">{value === null ? '—' : formatNumber(value)}</div>
    </div>
  )
}
