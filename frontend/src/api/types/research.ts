export type ResearchProvider = 'grok-x-research' | 'ai-trading-board'

export interface ResearchArtifact {
  id: string
  symbol: string
  provider: ResearchProvider
  headline: string
  body: string
  source_id: string
  published_at: string
  reviewed_by: string | null
}

export interface ResearchArtifactListResponse {
  items: ResearchArtifact[]
  count: number
}
