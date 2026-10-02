import { FileTextIcon } from 'lucide-react'
import { useState } from 'react'
import { useResearchArtifacts } from '@/api/queries/research'
import type { ResearchArtifact } from '@/api/types/research'
import { Button } from '@/components/ui/Button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { EmptyState, ErrorState } from '@/components/ui/EmptyState'
import { Input } from '@/components/ui/Input'
import { SkeletonRows } from '@/components/ui/Skeleton'
import { formatDateTime } from '@/lib/format'

export function ResearchPage() {
  const [input, setInput] = useState('')
  const [symbol, setSymbol] = useState<string | undefined>()
  const { data, isLoading, isError, error } = useResearchArtifacts(symbol)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-lg font-semibold text-text-primary">Research</h1>
        <p className="text-sm text-text-secondary">
          Reviewed Grok X reports and Trading Board analyses that inform the news analysis for a symbol.
        </p>
      </div>

      <Card>
        <CardContent className="pt-4">
          <form
            className="flex gap-2"
            onSubmit={(e) => {
              e.preventDefault()
              setSymbol(input.trim().toUpperCase() || undefined)
            }}
          >
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value.toUpperCase())}
              placeholder="Symbol, e.g. AAPL"
              maxLength={16}
              className="max-w-xs"
            />
            <Button type="submit">Find research</Button>
          </form>
        </CardContent>
      </Card>

      {isLoading && <SkeletonRows rows={4} />}
      {isError && <ErrorState message={(error as Error).message} />}
      {!symbol && (
        <EmptyState
          icon={FileTextIcon}
          title="Search a symbol"
          description="Enter a ticker above to see the reviewed research imported for it."
        />
      )}
      {data && data.items.length === 0 && (
        <EmptyState
          icon={FileTextIcon}
          title={`No reviewed research for ${symbol}`}
          description="Import a report with scripts/import_research.py."
        />
      )}
      {data && data.items.length > 0 && (
        <div className="space-y-4">
          {data.items.map((artifact) => (
            <ArtifactCard key={artifact.id} artifact={artifact} />
          ))}
        </div>
      )}
    </div>
  )
}

function ArtifactCard({ artifact }: { artifact: ResearchArtifact }) {
  return (
    <Card>
      <CardHeader className="flex-wrap">
        <CardTitle className="break-words">{artifact.headline}</CardTitle>
        <span className="text-xs text-text-secondary">{formatDateTime(artifact.published_at)}</span>
      </CardHeader>
      <CardContent className="space-y-3 text-sm">
        <p className="text-text-secondary">
          <span className="font-medium text-text-primary">{artifact.symbol}</span> · {artifact.provider} · reviewed by{' '}
          {artifact.reviewed_by ?? 'unknown'}
        </p>
        <details>
          <summary className="cursor-pointer text-xs font-medium text-series-1">Read source report</summary>
          <pre className="scroll-thin mt-2 max-h-96 overflow-auto whitespace-pre-wrap break-words rounded-md bg-surface-2 p-3 text-xs text-text-secondary">
            {artifact.body}
          </pre>
        </details>
      </CardContent>
    </Card>
  )
}
