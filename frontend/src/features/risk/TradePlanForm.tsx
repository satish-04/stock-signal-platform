import { useState } from 'react'
import { toast } from 'sonner'
import { useCreateOrderIntent } from '@/api/queries/orderIntents'
import { useEvaluateTradePlan } from '@/api/queries/risk'
import type { OptionType, TradeAction, TradePlanRequest } from '@/api/types/risk'
import { Button } from '@/components/ui/Button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { ErrorState } from '@/components/ui/EmptyState'
import { Input, Label, Select } from '@/components/ui/Input'
import { StatusBadge } from '@/components/ui/StatusBadge'
import { formatCurrency, formatNumber, formatPercent } from '@/lib/format'
import { useOrdersStore } from '@/store/ordersStore'

const DEFAULT_LIMITS = {
  account_equity: '100000',
  available_funds: '50000',
  max_risk_per_trade_pct: '0.50',
  max_position_value_pct: '2.0',
  max_contracts: 5,
  max_bid_ask_spread_pct: '5.0',
  minimum_open_interest: 1000,
  minimum_volume: 250,
  minimum_reward_risk_ratio: '2.0',
}

interface TradePlanFormState {
  symbol: string
  option_symbol: string
  option_type: OptionType
  expiry: string
  strike: string
  multiplier: number
  bid: string
  ask: string
  last: string
  volume: number
  open_interest: number
  action: TradeAction
  confidence: string
  stop_loss_pct: string
  first_target_pct: string
  second_target_pct: string
}

const DEFAULT_FORM: TradePlanFormState = {
  symbol: '',
  option_symbol: '',
  option_type: 'CALL',
  expiry: '',
  strike: '',
  multiplier: 100,
  bid: '',
  ask: '',
  last: '',
  volume: 0,
  open_interest: 0,
  action: 'BUY_CALL',
  confidence: '75',
  stop_loss_pct: '20',
  first_target_pct: '40',
  second_target_pct: '80',
}

export function TradePlanForm() {
  const [form, setForm] = useState<TradePlanFormState>(DEFAULT_FORM)
  const evaluate = useEvaluateTradePlan()
  const createIntent = useCreateOrderIntent()
  const addIntent = useOrdersStore((s) => s.addIntent)

  const set = <K extends keyof typeof form>(key: K, value: (typeof form)[K]) =>
    setForm((f) => ({ ...f, [key]: value }))

  const submit = (e: React.FormEvent) => {
    e.preventDefault()
    const request: TradePlanRequest = { ...form, limits: DEFAULT_LIMITS }
    evaluate.mutate(request, {
      onError: (err) => toast.error(err instanceof Error ? err.message : 'Trade plan evaluation failed'),
    })
  }

  const sendToOrders = () => {
    if (!evaluate.data) return
    createIntent.mutate(evaluate.data, {
      onSuccess: (intent) => {
        addIntent({
          intentId: intent.intent_id,
          symbol: intent.symbol,
          optionSymbol: intent.option_symbol,
          side: intent.side,
          quantity: intent.quantity,
          createdAt: new Date().toISOString(),
        })
        toast.success(`Order intent created (${intent.status})`)
      },
      onError: (err) => toast.error(err instanceof Error ? err.message : 'Failed to create order intent'),
    })
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Trade plan builder</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={submit} className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
          <Field label="Symbol">
            <Input required value={form.symbol} onChange={(e) => set('symbol', e.target.value.toUpperCase())} />
          </Field>
          <Field label="Option symbol">
            <Input required value={form.option_symbol} onChange={(e) => set('option_symbol', e.target.value)} />
          </Field>
          <Field label="Type">
            <Select value={form.option_type} onChange={(e) => set('option_type', e.target.value as OptionType)}>
              <option value="CALL">CALL</option>
              <option value="PUT">PUT</option>
            </Select>
          </Field>
          <Field label="Expiry">
            <Input required placeholder="20250620" value={form.expiry} onChange={(e) => set('expiry', e.target.value)} />
          </Field>
          <Field label="Strike">
            <Input required type="number" step="0.01" value={form.strike} onChange={(e) => set('strike', e.target.value)} />
          </Field>
          <Field label="Bid">
            <Input required type="number" step="0.01" value={form.bid} onChange={(e) => set('bid', e.target.value)} />
          </Field>
          <Field label="Ask">
            <Input required type="number" step="0.01" value={form.ask} onChange={(e) => set('ask', e.target.value)} />
          </Field>
          <Field label="Last">
            <Input required type="number" step="0.01" value={form.last} onChange={(e) => set('last', e.target.value)} />
          </Field>
          <Field label="Volume">
            <Input required type="number" value={form.volume} onChange={(e) => set('volume', Number(e.target.value))} />
          </Field>
          <Field label="Open interest">
            <Input
              required
              type="number"
              value={form.open_interest}
              onChange={(e) => set('open_interest', Number(e.target.value))}
            />
          </Field>
          <Field label="Action">
            <Select value={form.action} onChange={(e) => set('action', e.target.value as TradeAction)}>
              <option value="BUY_CALL">BUY_CALL</option>
              <option value="BUY_PUT">BUY_PUT</option>
              <option value="HOLD">HOLD</option>
            </Select>
          </Field>
          <Field label="Confidence %">
            <Input required type="number" value={form.confidence} onChange={(e) => set('confidence', e.target.value)} />
          </Field>
          <Field label="Stop loss %">
            <Input required type="number" value={form.stop_loss_pct} onChange={(e) => set('stop_loss_pct', e.target.value)} />
          </Field>
          <Field label="1st target %">
            <Input required type="number" value={form.first_target_pct} onChange={(e) => set('first_target_pct', e.target.value)} />
          </Field>
          <Field label="2nd target %">
            <Input
              required
              type="number"
              value={form.second_target_pct}
              onChange={(e) => set('second_target_pct', e.target.value)}
            />
          </Field>

          <div className="col-span-full">
            <Button type="submit" disabled={evaluate.isPending}>
              {evaluate.isPending ? 'Evaluating…' : 'Evaluate trade plan'}
            </Button>
          </div>
        </form>

        {evaluate.isError && <ErrorState message={(evaluate.error as Error).message} />}

        {evaluate.data && (
          <div className="mt-6 space-y-3 border-t border-border pt-4">
            <div className="flex flex-wrap items-center gap-2">
              <StatusBadge status={evaluate.data.decision} />
              <span className="text-sm text-text-secondary">
                {evaluate.data.side} {evaluate.data.quantity}x {evaluate.data.option_symbol}
              </span>
            </div>
            <div className="grid grid-cols-2 gap-2 tabular-nums sm:grid-cols-4">
              <Metric label="Limit price" value={formatCurrency(evaluate.data.limit_price)} />
              <Metric label="Est. debit" value={formatCurrency(evaluate.data.estimated_debit)} />
              <Metric label="Max loss" value={formatCurrency(evaluate.data.maximum_loss)} />
              <Metric label="R:R" value={formatNumber(evaluate.data.reward_risk_ratio)} />
              <Metric label="Stop" value={formatCurrency(evaluate.data.stop_price)} />
              <Metric label="Target 1" value={formatCurrency(evaluate.data.first_target_price)} />
              <Metric label="Target 2" value={formatCurrency(evaluate.data.second_target_price)} />
              <Metric label="Account risk" value={formatPercent(evaluate.data.account_risk_pct)} />
            </div>
            {evaluate.data.reasons.length > 0 && (
              <ul className="list-inside list-disc text-sm text-text-secondary">
                {evaluate.data.reasons.map((r) => (
                  <li key={r}>{r}</li>
                ))}
              </ul>
            )}
            {evaluate.data.rejection_reasons.length > 0 && (
              <ul className="list-inside list-disc text-sm text-status-critical">
                {evaluate.data.rejection_reasons.map((r) => (
                  <li key={r}>{r}</li>
                ))}
              </ul>
            )}
            {evaluate.data.decision === 'APPROVED' && (
              <Button onClick={sendToOrders} disabled={createIntent.isPending} variant="secondary">
                {createIntent.isPending ? 'Sending…' : 'Send to orders'}
              </Button>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <Label>{label}</Label>
      {children}
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
