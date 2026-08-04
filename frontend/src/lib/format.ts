export function toNumber(value: string | number | null | undefined): number | null {
  if (value === null || value === undefined || value === '') return null
  const parsed = typeof value === 'number' ? value : Number.parseFloat(value)
  return Number.isNaN(parsed) ? null : parsed
}

export function formatCurrency(value: string | number | null | undefined, fractionDigits = 2): string {
  const n = toNumber(value)
  if (n === null) return '—'
  return n.toLocaleString('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: fractionDigits,
    maximumFractionDigits: fractionDigits,
  })
}

export function formatSignedCurrency(value: string | number | null | undefined, fractionDigits = 2): string {
  const n = toNumber(value)
  if (n === null) return '—'
  const formatted = formatCurrency(Math.abs(n), fractionDigits)
  if (n > 0) return `+${formatted}`
  if (n < 0) return `-${formatted}`
  return formatted
}

export function formatNumber(value: string | number | null | undefined, fractionDigits = 2): string {
  const n = toNumber(value)
  if (n === null) return '—'
  return n.toLocaleString('en-US', {
    minimumFractionDigits: fractionDigits,
    maximumFractionDigits: fractionDigits,
  })
}

export function formatPercent(value: string | number | null | undefined, fractionDigits = 1): string {
  const n = toNumber(value)
  if (n === null) return '—'
  return `${n.toFixed(fractionDigits)}%`
}

export function formatInteger(value: string | number | null | undefined): string {
  const n = toNumber(value)
  if (n === null) return '—'
  return n.toLocaleString('en-US')
}

export function formatDateTime(value: string | null | undefined): string {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '—'
  return date.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  })
}

export function formatRelativeTime(value: string | null | undefined): string {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '—'
  const diffMs = date.getTime() - Date.now()
  const diffSec = Math.round(diffMs / 1000)
  const abs = Math.abs(diffSec)

  const units: [Intl.RelativeTimeFormatUnit, number][] = [
    ['year', 31536000],
    ['month', 2592000],
    ['day', 86400],
    ['hour', 3600],
    ['minute', 60],
    ['second', 1],
  ]
  const rtf = new Intl.RelativeTimeFormat('en', { numeric: 'auto' })
  for (const [unit, secondsInUnit] of units) {
    if (abs >= secondsInUnit || unit === 'second') {
      return rtf.format(Math.round(diffSec / secondsInUnit), unit)
    }
  }
  return '—'
}

export function truncateMiddle(value: string, maxLength = 12): string {
  if (value.length <= maxLength) return value
  const keep = Math.floor((maxLength - 1) / 2)
  return `${value.slice(0, keep)}…${value.slice(value.length - keep)}`
}
