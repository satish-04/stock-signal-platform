import { AIRecommendationPanel } from './AIRecommendationPanel'
import { TradePlanForm } from './TradePlanForm'

export function RiskPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-lg font-semibold text-text-primary">Risk & AI</h1>
        <p className="text-sm text-text-secondary">Evaluate trade plans against risk limits, or ask for an AI-generated recommendation.</p>
      </div>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
        <TradePlanForm />
        <AIRecommendationPanel />
      </div>
    </div>
  )
}
