import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api, endpoints, type ScannerResult } from '../lib/types'

const MarketScannerPage = () => {
  const [selectedFilter, setSelectedFilter] = useState('All')
  
  const { data: scannerData = [] } = useQuery<ScannerResult[]>({
    queryKey: ['scanner', selectedFilter],
    queryFn: () => api.get<ScannerResult[]>(endpoints.scanner),
  })

  const results = scannerData.length > 0 ? scannerData : [
    { ticker: 'AAPL', price: 175.23, change: '+1.2%', volume: '45M', signal: 'bullish' as const },
    { ticker: 'NVDA', price: 923.45, change: '-0.8%', volume: '32M', signal: 'bearish' as const },
    { ticker: 'TSLA', price: 245.67, change: '+2.1%', volume: '28M', signal: 'bullish' as const },
    { ticker: 'AMD', price: 178.32, change: '+3.4%', volume: '67M', signal: 'bullish' as const },
    { ticker: 'META', price: 485.67, change: '+0.5%', volume: '23M', signal: 'bullish' as const },
    { ticker: 'MSFT', price: 392.12, change: '-0.5%', volume: '34M', signal: 'neutral' as const },
    { ticker: 'AMZN', price: 145.89, change: '+0.9%', volume: '21M', signal: 'bullish' as const },
    { ticker: 'GOOGL', price: 142.34, change: '-1.1%', volume: '18M', signal: 'bearish' as const },
    { ticker: 'NFLX', price: 489.23, change: '+1.7%', volume: '15M', signal: 'bullish' as const },
    { ticker: 'INTC', price: 58.45, change: '-2.3%', volume: '29M', signal: 'bearish' as const },
  ]

  const filteredResults = results.filter((result) => {
    if (selectedFilter === 'All') return true
    if (selectedFilter === 'Bullish' || selectedFilter === 'Bearish' || selectedFilter === 'Neutral') {
      return result.signal === selectedFilter.toLowerCase()
    }
    if (selectedFilter === 'High Volume') {
      const vol = parseInt(result.volume.replace('M', ''))
      return vol > 50
    }
    if (selectedFilter === 'Big Movers') {
      const change = parseFloat(result.change)
      return Math.abs(change) > 1.5
    }
    if (selectedFilter === 'Gainers') return result.change.startsWith('+')
    if (selectedFilter === 'Losers') return result.change.startsWith('-')
    return true
  })

  // Calculate summary stats
  const gainers = filteredResults.filter(r => r.change.startsWith('+'))
  const losers = filteredResults.filter(r => !r.change.startsWith('+'))

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Market Scanner</h1>
          <p className="text-gray-500 mt-1">Real-time market scanner for trading opportunities</p>
        </div>

        <div className="flex gap-3">
          <select
            value={selectedFilter}
            onChange={(e) => setSelectedFilter(e.target.value)}
            className="input-base px-4 py-2 min-w-[180px]"
          >
            <option value="All">All Symbols</option>
            <option value="Bullish">Bullish Signals Only</option>
            <option value="Bearish">Bearish Signals Only</option>
            <option value="Neutral">Neutral Signals Only</option>
            <option value="Gainers">Top Gainers</option>
            <option value="Losers">Top Losers</option>
            <option value="High Volume">High Volume (&gt;50M)</option>
          </select>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="card bg-green-50 border-green-200">
          <h3 className="text-sm font-semibold text-green-800 mb-2">Bullish Signals</h3>
          <p className="text-3xl font-bold text-green-600">{gainers.length}</p>
        </div>

        <div className="card bg-red-50 border-red-200">
          <h3 className="text-sm font-semibold text-red-800 mb-2">Bearish Signals</h3>
          <p className="text-3xl font-bold text-red-600">{losers.length}</p>
        </div>

        <div className="card bg-blue-50 border-blue-200">
          <h3 className="text-sm font-semibold text-blue-800 mb-2">Avg. Volume</h3>
          <p className="text-3xl font-bold text-blue-600">32M</p>
        </div>

        <div className="card bg-purple-50 border-purple-200">
          <h3 className="text-sm font-semibold text-purple-800 mb-2">Scanned</h3>
          <p className="text-3xl font-bold text-purple-600">{results.length}</p>
        </div>
      </div>

      {/* Scanner Results */}
      <div className="card">
        <div className="mb-6 flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">Scanned Results</h3>
          <span className="text-sm text-gray-500">
            Showing {filteredResults.length} of {results.length} symbols
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-200 bg-gray-50">
                <th className="table-header">Symbol</th>
                <th className="table-header">Price</th>
                <th className="table-header">Change</th>
                <th className="table-header">Volume</th>
                <th className="table-header">Signal</th>
                <th className="table-header text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {filteredResults.map((result, idx) => (
                <tr
                  key={idx}
                  className="hover:bg-gray-50 transition-colors group cursor-pointer"
                >
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center gap-3">
                      <div
                        className={`w-10 h-10 rounded-lg flex items-center justify-center font-bold text-white ${
                          result.signal === 'bullish'
                            ? 'bg-green-500'
                            : result.signal === 'bearish'
                            ? 'bg-red-500'
                            : 'bg-gray-400'
                        }`}
                      >
                        {result.ticker.slice(0, 1)}
                      </div>
                      <span className="font-semibold text-gray-900">{result.ticker}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    ${result.price.toFixed(2)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span
                      className={`font-medium ${
                        result.change.startsWith('+') ? 'text-green-600' : 'text-red-600'
                      }`}
                    >
                      {result.change}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                    {result.volume}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span
                      className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${
                        result.signal === 'bullish'
                          ? 'bg-green-100 text-green-800 border border-green-200'
                          : result.signal === 'bearish'
                          ? 'bg-red-100 text-red-800 border border-red-200'
                          : 'bg-gray-100 text-gray-800 border border-gray-200'
                      }`}
                    >
                      {result.signal.charAt(0).toUpperCase() + result.signal.slice(1)}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right">
                    <button
                      className={`btn-primary inline-block px-3 py-1.5 text-sm ${
                        result.signal === 'bullish'
                          ? 'bg-green-600 hover:bg-green-700'
                          : result.signal === 'bearish'
                          ? 'bg-red-600 hover:bg-red-700'
                          : ''
                      }`}
                    >
                      Trade
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {filteredResults.length === 0 && (
            <div className="py-12 text-center">
              <p className="text-gray-500">No symbols match your filter</p>
            </div>
          )}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="card bg-gradient-to-br from-blue-50 to-purple-50 border-blue-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Market Sentiment</h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between text-sm p-2 bg-white rounded-lg border">
              <span className="text-gray-700">Bullish</span>
              <div className="flex items-center gap-3">
                <div className="w-full bg-gray-200 rounded-full h-2 flex-1">
                  <div className="h-2 rounded-full bg-green-500" style={{ width: '45%' }}></div>
                </div>
                <span className="font-bold text-green-600">45%</span>
              </div>
            </div>

            <div className="flex items-center justify-between text-sm p-2 bg-white rounded-lg border">
              <span className="text-gray-700">Bearish</span>
              <div className="flex items-center gap-3">
                <div className="w-full bg-gray-200 rounded-full h-2 flex-1">
                  <div className="h-2 rounded-full bg-red-500" style={{ width: '30%' }}></div>
                </div>
                <span className="font-bold text-red-600">30%</span>
              </div>
            </div>

            <div className="flex items-center justify-between text-sm p-2 bg-white rounded-lg border">
              <span className="text-gray-700">Neutral</span>
              <div className="flex items-center gap-3">
                <div className="w-full bg-gray-200 rounded-full h-2 flex-1">
                  <div className="h-2 rounded-full bg-gray-500" style={{ width: '25%' }}></div>
                </div>
                <span className="font-bold text-gray-600">25%</span>
              </div>
            </div>
          </div>
        </div>

        <div className="card bg-gradient-to-br from-green-50 to-emerald-50 border-green-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Top Opportunities</h3>
          <div className="space-y-3">
            {[
              { ticker: 'AAPL', reason: 'Bollinger Band breakouts', action: 'Buy' },
              { ticker: 'AMD', reason: 'Volume spike detected', action: 'Buy' },
              { ticker: 'TSLA', reason: 'EMA crossover bullish', action: 'Buy' },
            ].map((item, idx) => (
              <div key={idx} className="flex items-center justify-between p-3 bg-white rounded-lg border">
                <div>
                  <span className="font-bold text-gray-900">{item.ticker}</span>
                  <div className="text-xs text-green-600 mt-1">{item.reason}</div>
                </div>
                <button className="btn-primary text-xs px-2 py-1">{item.action}</button>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

export default MarketScannerPage