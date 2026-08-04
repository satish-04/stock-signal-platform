import { useState } from 'react'
import { toast } from 'sonner'
import { useMarkPosition } from '@/api/queries/positions'
import type { PositionResponse } from '@/api/types/positions'
import { Button } from '@/components/ui/Button'
import { Drawer } from '@/components/ui/Drawer'
import { Input, Label } from '@/components/ui/Input'
import { formatCurrency } from '@/lib/format'

export function MarkPositionDrawer({
  position,
  accountId,
  onClose,
}: {
  position: PositionResponse | null
  accountId: string
  onClose: () => void
}) {
  const [markPrice, setMarkPrice] = useState('')
  const mutation = useMarkPosition(accountId)

  const submit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!position || !markPrice) return
    mutation.mutate(
      { positionId: position.position_id, markPrice },
      {
        onSuccess: () => {
          toast.success(`${position.symbol} marked at ${formatCurrency(markPrice)}`)
          setMarkPrice('')
          onClose()
        },
        onError: (err) => toast.error(err instanceof Error ? err.message : 'Failed to mark position'),
      },
    )
  }

  return (
    <Drawer open={!!position} onClose={onClose} title={position ? `Mark ${position.symbol}` : ''}>
      {position && (
        <form onSubmit={submit} className="space-y-4">
          <div className="space-y-1 text-sm text-text-secondary">
            <p>
              Option: <span className="text-text-primary">{position.option_symbol}</span>
            </p>
            <p>
              Current mark: <span className="text-text-primary">{formatCurrency(position.current_mark_price)}</span>
            </p>
          </div>
          <div>
            <Label htmlFor="mark-price">New mark price</Label>
            <Input
              id="mark-price"
              type="number"
              step="0.01"
              min="0"
              required
              value={markPrice}
              onChange={(e) => setMarkPrice(e.target.value)}
              placeholder="0.00"
            />
          </div>
          <Button type="submit" disabled={mutation.isPending} className="w-full">
            {mutation.isPending ? 'Submitting…' : 'Submit mark'}
          </Button>
        </form>
      )}
    </Drawer>
  )
}
