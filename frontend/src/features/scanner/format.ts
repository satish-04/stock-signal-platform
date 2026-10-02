import { formatPercent } from '@/lib/format'

export function formatExpiry(iso: string): string {
  return new Date(`${iso}T00:00:00`).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })
}

/** The API reports implied volatility as a fraction; null means it could not be solved. */
export function formatIv(value: number | null): string {
  return formatPercent(value === null ? null : value * 100, 0)
}
