import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api, endpoints, type Option } from '../lib/types'

const OptionChainPage = () => {
  const [selectedTicker, setSelectedTicker] = useState('AAPL')
  const [expiryFilter, setExpiryFilter] = useState('This Week')
  
  const { data: optionsData = [] } = useQuery<Option[]>({
    queryKey: ['options', selectedTicker],
    queryFn: () => api.get<Option[]>(endpoints.options),
  })

  const options = optionsData.length > 0 ? optionsData : [
    { id: 1, ticker: 'AAPL', expiry: '2024-12-20', strike: 175, type: 'call' as const, bid: 3.45, ask: 3.60, iv: 28.5, delta: 0.45 },
    { id: 2, ticker: 'AAPL', expiry: '2024-12-20', strike: 175, type: 'put' as const, bid: 2.80, ask: 2.95, iv: 31.2, delta: -0.38 },
    { id: 3, ticker: 'NVDA', expiry: '2024-12-27', strike: 950, type: 'call' as const, bid: 8.10, ask: 8.35, iv: 32.8, delta: 0.55 },
    { id: 4, ticker: 'TSLA', expiry: '2025-01-17', strike: 240, type: 'put' as const, bid: 4.50, ask: 4.70, iv: 29.1, delta: -0.42 },
    { id: 5, ticker: 'AAPL', expiry: '2024-12-27', strike: 180, type: 'call' as const, bid: 2.15, ask: 2.30, iv: 27.8, delta: 0.35 },
    { id: 6, ticker: 'AAPL', expiry: '2024-12-27', strike: 180, type: 'put' as const, bid: 3.25, ask: 3.40, iv: 30.1, delta: -0.42 },
  ]

  const filteredOptions = options.filter((option) => 
    option.ticker === selectedTicker
  )

  const groupedByExpiry: Record<string, Option[]> = {}
  filteredOptions.forEach((option) => {
    if (!groupedByExpiry[option.expiry]) {
      groupedByExpiry[option.expiry] = []
    }
    groupedByExpiry[option.expiry].push(option)
  })

  const expiries = Object.keys(groupedByExpiry)

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Option Chain</h1>
          <p className="text-gray-500 mt-1">View real-time options data with greeks</p>
        </div>

        <div className="flex gap-3">
          <select
            value={selectedTicker}
            onChange={(e) => setSelectedTicker(e.target.value)}
            className="input-base px-4 py-2 min-w-[150px]"
          >
            <option value="AAPL">Apple (AAPL)</option>
            <option value="NVDA">NVIDIA (NVDA)</option>
            <option value="TSLA">Tesla (TSLA)</option>
            <option value="AMD">AMD (AMD)</option>
            <option value="META">Meta (META)</option>
          </select>

          <select
            value={expiryFilter}
            onChange={(e) => setExpiryFilter(e.target.value)}
            className="input-base px-4 py-2 min-w-[150px]"
          >
            <option value="This Week">This Week</option>
            <option value="Next Week">Next Week</option>
            <option value="This Month">This Month</option>
          </select>
        </div>
      </div>

      {/* Ticker Info */}
      <div className="card flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center text-white font-bold text-3xl">
            {selectedTicker.slice(0, 1)}
          </div>
          <div>
            <h2 className="text-2xl font-bold text-gray-900">{selectedTicker}</h2>
            <p className="text-sm text-gray-500">Call/Put Options Chain</p>
          </div>
        </div>

        <div className="text-right">
          <div className="text-sm text-gray-500">Underlying Price</div>
          <div className="text-xl font-bold text-blue-600">
            ${175.23.toFixed(2)} <span className="text-green-600 text-sm">+1.2%</span>
          </div>
        </div>
      </div>

      {/* Option Chains */}
      <div className="grid gap-6">
        {expiries.length > 0 ? (
          expiries.map((expiry) => {
            const expiryOptions = groupedByExpiry[expiry]
            const calls = expiryOptions.filter(o => o.type === 'call')
            const puts = expiryOptions.filter(o => o.type === 'put')

            return (
              <div key={expiry} className="card">
                {/* Expiry Header */}
                <div className="flex items-center justify-between mb-6 pb-4 border-b border-gray-200">
                  <div className="flex items-center gap-3">
                    <span className="text-sm font-semibold text-blue-600">Expiry: {expiry}</span>
                    <div className="w-px h-4 bg-gray-300"></div>
                    <span className="text-sm text-gray-500">
                      {calls.length} Calls / {puts.length} Puts
                    </span>
                  </div>
                </div>

                {/* Options Table */}
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-gray-200 bg-gray-50">
                        <th className="table-header">Strike</th>
                        <th colSpan={2} className="text-center border-b-2 border-green-300 pb-2">
                          <span className="text-sm font-bold text-green-600">CALLS</span>
                        </th>
                        <th colSpan={2} className="text-center border-b-2 border-red-300 pb-2">
                          <span className="text-sm font-bold text-red-600">PUTS</span>
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {calls.map((call, idx) => {
                        const put = puts[idx]
                        return (
                          <tr key={call.strike} className="hover:bg-gray-50 transition-colors">
                            <td className="px-6 py-4 whitespace-nowrap font-semibold text-gray-900">
                              ${call.strike.toFixed(2)}
                            </td>
                            
                            {/* Call BID/ASK */}
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="text-sm font-medium text-green-600">{call.bid}</div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="text-sm text-green-500">{call.ask}</div>
                            </td>

                            {/* Put BID/ASK */}
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="text-sm font-medium text-red-600">{put?.bid}</div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="text-sm text-red-500">{put?.ask}</div>
                            </td>

                            {/* Greeks for Call */}
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="text-xs text-green-500">IV: {call.iv?.toFixed(1)}</div>
                              <div className="text-xs text-green-500">Δ: {call.delta?.toFixed(2)}</div>
                            </td>

                            {/* Greeks for Put */}
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="text-xs text-red-500">IV: {put?.iv?.toFixed(1) || 'N/A'}</div>
                              <div className="text-xs text-red-500">Δ: {put?.delta?.toFixed(2) || 'N/A'}</div>
                            </td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>

                {calls.length === 0 && (
                  <div className="py-8 text-center text-gray-500">No options data available for this expiry</div>
                )}
              </div>
            )
          })
        ) : (
          <div className="card py-12 text-center">
            <p className="text-gray-500">No options data available for {selectedTicker}</p>
          </div>
        )}
      </div>

      {/* Greeks Legend */}
      <div className="card bg-blue-50 border-blue-100">
        <h3 className="text-sm font-semibold text-blue-900 mb-3">Greeks Reference</h3>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          {[
            { name: 'Delta', desc: 'Price change per $1 stock move' },
            { name: 'Gamma', desc: 'Rate of delta change per $1 stock move' },
            { name: 'Theta', desc: 'Daily time decay' },
            { name: 'Vega', desc: 'Price change per 1% IV change' },
            { name: 'IV', desc: 'Implied volatility percentage' },
          ].map((greek) => (
            <div key={greek.name} className="flex flex-col">
              <span className="font-semibold text-blue-700">{greek.name}</span>
              <span className="text-xs text-blue-600 mt-1">{greek.desc}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default OptionChainPage