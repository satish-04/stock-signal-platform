import type { ScanItem, ScanStrike } from '@/api/types/scanner'
import { Drawer } from '@/components/ui/Drawer'
import { formatCompact, formatCurrency, formatNumber, formatPercent } from '@/lib/format'
import { formatExpiry, formatIv } from './format'

export function StrikeDetailDrawer({ item, onClose }: { item: ScanItem | null; onClose: () => void }) {
  return (
    <Drawer open={!!item} onClose={onClose} title={item ? `${item.symbol} · ${formatExpiry(item.expiry)} expiry` : ''}>
      {item && (
        <div className="space-y-5 text-sm">
          <div className="grid grid-cols-3 gap-2 tabular-nums">
            <Metric label="Last" value={formatNumber(item.spot)} />
            <Metric label="Contracts" value={formatCompact(item.total_volume)} />
            <Metric label="Put/call" value={formatNumber(item.put_call_ratio)} />
            <Metric label="ATM strike" value={String(item.atm_strike)} />
            <Metric label="ATM IV" value={formatIv(item.atm_iv)} />
            <Metric label="Implied move" value={`±${formatPercent(item.implied_move_pct)}`} />
          </div>

          <StrikeTable title="Most-traded calls" strikes={item.top_calls} />
          <StrikeTable title="Most-traded puts" strikes={item.top_puts} />

          <p className="text-xs text-text-muted">
            Premium is contracts × last price × 100. A strike can trade tens of thousands of contracts at a cent
            each, so compare premium, not only contract counts.
          </p>
        </div>
      )}
    </Drawer>
  )
}

function StrikeTable({ title, strikes }: { title: string; strikes: ScanStrike[] }) {
  return (
    <div>
      <h3 className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-text-muted">{title}</h3>
      {strikes.length === 0 ? (
        <p className="text-text-secondary">No contracts traded.</p>
      ) : (
        <table className="w-full border-collapse text-xs tabular-nums">
          <thead>
            <tr className="border-b border-border text-left text-text-muted">
              <th className="py-1.5 pr-2 font-medium">Strike</th>
              <th className="py-1.5 pr-2 font-medium">Contracts</th>
              <th className="py-1.5 pr-2 font-medium">Open int.</th>
              <th className="py-1.5 pr-2 font-medium">Last</th>
              <th className="py-1.5 pr-2 font-medium">IV</th>
              <th className="py-1.5 pr-2 font-medium">Delta</th>
              <th className="py-1.5 font-medium">Premium</th>
            </tr>
          </thead>
          <tbody>
            {strikes.map((strike) => (
              <tr key={strike.strike} className="border-b border-border last:border-0">
                <td className="py-1.5 pr-2 font-medium text-text-primary">{strike.strike}</td>
                <td className="py-1.5 pr-2 text-text-primary">{formatCompact(strike.volume)}</td>
                <td className="py-1.5 pr-2 text-text-primary">{formatCompact(strike.open_interest)}</td>
                <td className="py-1.5 pr-2 text-text-primary">{formatNumber(strike.last)}</td>
                <td className="py-1.5 pr-2 text-text-primary">{formatIv(strike.implied_volatility)}</td>
                <td className="py-1.5 pr-2 text-text-primary">{formatNumber(strike.delta)}</td>
                <td className="py-1.5 text-text-primary">{formatCurrency(strike.premium, 0)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
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
