import type { BacktestResponse } from '@/api/types/quant'

const WIDTH = 720
const HEIGHT = 220
const PAD = { top: 12, right: 78, bottom: 22, left: 8 }

/** Growth of 1 unit: the best full-sample parameters against buy and hold. */
export function EquityCurve({ curve }: { curve: BacktestResponse['equity_curve'] }) {
  if (curve.length < 2) return null
  const values = curve.flatMap((point) => [point.strategy, point.benchmark])
  const low = Math.min(...values, 1)
  const high = Math.max(...values, 1)
  const x = (index: number) => PAD.left + (index / (curve.length - 1)) * (WIDTH - PAD.left - PAD.right)
  const y = (value: number) => PAD.top + (1 - (value - low) / (high - low || 1)) * (HEIGHT - PAD.top - PAD.bottom)
  const path = (key: 'strategy' | 'benchmark') =>
    curve.map((point, index) => `${index ? 'L' : 'M'}${x(index).toFixed(1)},${y(point[key]).toFixed(1)}`).join(' ')
  const last = curve[curve.length - 1]
  const labelX = WIDTH - PAD.right + 6
  // Keep the two end labels from overlapping when the lines finish close together.
  const gap = y(last.strategy) - y(last.benchmark)
  const nudge = Math.abs(gap) < 14 ? (gap >= 0 ? 7 : -7) : 0

  return (
    <svg
      viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
      className="w-full"
      role="img"
      aria-label={`Growth of 1: strategy ends at ${last.strategy.toFixed(2)}, buy and hold at ${last.benchmark.toFixed(2)}`}
    >
      <line x1={PAD.left} x2={WIDTH - PAD.right} y1={y(1)} y2={y(1)} stroke="var(--baseline)" strokeDasharray="3 3" />
      <path d={path('benchmark')} fill="none" stroke="var(--text-muted)" strokeWidth="1.5" />
      <path d={path('strategy')} fill="none" stroke="var(--series-1)" strokeWidth="2" />
      <text x={labelX} y={y(last.strategy) + 4 + nudge} fontSize="11" fill="var(--series-1)">
        Strategy {last.strategy.toFixed(2)}
      </text>
      <text x={labelX} y={y(last.benchmark) + 4 - nudge} fontSize="11" fill="var(--text-secondary)">
        Hold {last.benchmark.toFixed(2)}
      </text>
      <text x={PAD.left} y={HEIGHT - 6} fontSize="11" fill="var(--text-muted)">
        {curve[0].date}
      </text>
      <text x={WIDTH - PAD.right} y={HEIGHT - 6} fontSize="11" fill="var(--text-muted)" textAnchor="end">
        {last.date}
      </text>
    </svg>
  )
}
