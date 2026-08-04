import {
  CandlestickSeries,
  ColorType,
  createChart,
  LineStyle,
  type IChartApi,
  type ISeriesApi,
  type UTCTimestamp,
} from 'lightweight-charts'
import { useEffect, useRef } from 'react'

export interface Candle {
  time: UTCTimestamp
  open: number
  high: number
  low: number
  close: number
}

export interface PriceLevel {
  price: number
  color: string
  title: string
}

export function PriceChart({ candles, levels }: { candles: Candle[]; levels: PriceLevel[] }) {
  const containerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<IChartApi | null>(null)
  const seriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null)

  useEffect(() => {
    if (!containerRef.current) return
    const styles = getComputedStyle(document.documentElement)
    const textSecondary = styles.getPropertyValue('--text-secondary').trim()
    const gridline = styles.getPropertyValue('--gridline').trim()
    const surface = styles.getPropertyValue('--surface-1').trim()

    const chart = createChart(containerRef.current, {
      layout: { background: { type: ColorType.Solid, color: surface }, textColor: textSecondary },
      grid: { vertLines: { color: gridline }, horzLines: { color: gridline } },
      rightPriceScale: { borderColor: gridline },
      timeScale: { borderColor: gridline },
      autoSize: true,
    })
    const series = chart.addSeries(CandlestickSeries, {
      upColor: styles.getPropertyValue('--status-good').trim(),
      downColor: styles.getPropertyValue('--status-critical').trim(),
      borderVisible: false,
      wickUpColor: styles.getPropertyValue('--status-good').trim(),
      wickDownColor: styles.getPropertyValue('--status-critical').trim(),
    })

    chartRef.current = chart
    seriesRef.current = series

    return () => {
      chart.remove()
      chartRef.current = null
      seriesRef.current = null
    }
  }, [])

  useEffect(() => {
    if (!seriesRef.current) return
    seriesRef.current.setData(candles)
    chartRef.current?.timeScale().fitContent()
  }, [candles])

  useEffect(() => {
    const series = seriesRef.current
    if (!series) return
    const priceLines = levels.map((level) =>
      series.createPriceLine({
        price: level.price,
        color: level.color,
        lineWidth: 1,
        lineStyle: LineStyle.Dashed,
        axisLabelVisible: true,
        title: level.title,
      }),
    )
    return () => {
      priceLines.forEach((line) => series.removePriceLine(line))
    }
  }, [levels])

  return <div ref={containerRef} className="h-96 w-full" />
}
