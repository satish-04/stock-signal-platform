import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api, endpoints, type Signal } from '../lib/types'

const SignalCenterPage = () => {
  const [selectedFilter, setSelectedFilter] = useState('All')
  const [tickerSearch, setTickerSearch] = useState('')
  
  const { data: signalsData = [] } = useQuery<Signal[]>({
    queryKey: ['signals', selectedFilter, tickerSearch],
    queryFn: () => api.get<Signal[]>(endpoints.signals),
  })
  
  const signals = signalsData.length > 0 ? signalsData : [
    { id: 1, ticker: 'AAPL', type: 'bullish' as const, confidence: 0.87, price: 175.23, rsi: 65.4, action: 'buy' as const, quantity: 10, reason: 'EMA9 cross above EMA20', created_at: '2024-12-21T10:30:00Z' },
    { id: 2, ticker: 'NVDA', type: 'bearish' as const, confidence: 0.78, price: 923.45, rsi: 71.2, action: 'sell' as const, quantity: 5, reason: 'RSI > 70 overbought', created_at: '2024-12-21T09:45:00Z' },
    { id: 3, ticker: 'TSLA', type: 'bullish' as const, confidence: 0.82, price: 245.67, rsi: 58.9, action: 'buy' as const, quantity: 15, reason: 'Bollinger Band breakouts', created_at: '2024-12-21T11:15:00Z' },
    { id: 4, ticker: 'AMD', type: 'bullish' as const, confidence: 0.73, price: 178.32, rsi: 52.1, action: 'buy' as const, quantity: 20, reason: 'Volume spike with price breakout', created_at: '2024-12-21T10:00:00Z' },
    { id: 5, ticker: 'META', type: 'neutral' as const, confidence: 0.61, price: 485.67, rsi: 48.3, action: 'hold' as const, quantity: 0, reason: 'Consolidation pattern forming', created_at: '2024-12-21T11:30:00Z' },
  ]

  const filteredSignals = signals.filter((signal) => {
    if (selectedFilter !== 'All') {
      return signal.type === selectedFilter.toLowerCase()
    }
    if (tickerSearch) {
      return signal.ticker.toLowerCase().includes(tickerSearch.toLowerCase())
    }
    return true
  })

  const signalCounts = {
    All: signals.length,
    bullish: signals.filter(s => s.type === 'bullish').length,
    bearish: signals.filter(s => s.type === 'bearish').length,
    neutral: signals.filter(s => s.type === 'neutral').length,
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Signal Center</h1>
          <p className="text-gray-500 mt-1">AI-generated trading signals powered by technical analysis</p>
        </div>

        <div className="flex gap-3">
          <input
            type="text"
            placeholder="Search ticker..."
            value={tickerSearch}
            onChange={(e) => setTickerSearch(e.target.value)}
            className="input-base w-48"
          />
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
        <div className="flex flex-wrap items-center gap-3">
          <span className="text-sm font-medium text-gray-700">Filter:</span>
          
          {['All', 'bullish', 'bearish', 'neutral'].map((filter) => (
            <button
              key={filter}
              onClick={() => setSelectedFilter(filter)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                selectedFilter === filter
                  ? 'bg-blue-600 text-white shadow-lg'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {filter.charAt(0).toUpperCase() + filter.slice(1)}
              <span className="ml-2 px-2 py-0.5 bg-white/30 rounded-full text-xs">
                {signalCounts[filter as keyof typeof signalCounts]}
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 bg-blue-500 rounded-lg flex items-center justify-center text-white">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
              </svg>
            </div>
            <h3 className="text-lg font-bold text-blue-800">Bullish Signals</h3>
          </div>
          <p className="text-4xl font-bold text-blue-600">{signalCounts.bullish}</p>
          <p className="text-sm text-blue-600 mt-1">Strong buy recommendations</p>
        </div>

        <div className="card bg-gradient-to-br from-red-50 to-red-100 border-red-200">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 bg-red-500 rounded-lg flex items-center justify-center text-white">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6" />
              </svg>
            </div>
            <h3 className="text-lg font-bold text-red-800">Bearish Signals</h3>
          </div>
          <p className="text-4xl font-bold text-red-600">{signalCounts.bearish}</p>
          <p className="text-sm text-red-600 mt-1">Strong sell recommendations</p>
        </div>

        <div className="card bg-gradient-to-br from-gray-50 to-gray-100 border-gray-200">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 bg-gray-500 rounded-lg flex items-center justify-center text-white">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h3 className="text-lg font-bold text-gray-800">Neutral Signals</h3>
          </div>
          <p className="text-4xl font-bold text-gray-600">{signalCounts.neutral}</p>
          <p className="text-sm text-gray-600 mt-1">Hold positions</p>
        </div>
      </div>

      {/* Signals Table */}
      <div className="card">
        <div className="mb-6 flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">All Signals</h3>
          <span className="text-sm text-gray-500">
            Showing {filteredSignals.length} signals
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="table-header">Ticker</th>
                <th className="table-header">Type</th>
                <th className="table-header">Confidence</th>
                <th className="table-header">Price</th>
                <th className="table-header">RSI</th>
                <th className="table-header">Action</th>
                <th className="table-header">Reason</th>
                <th className="table-header text-right">Time</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {filteredSignals.map((signal) => (
                <tr key={signal.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center gap-3">
                      <div className={`w-10 h-10 rounded-lg flex items-center justify-center font-bold text-white ${
                        signal.type === 'bullish' ? 'bg-green-500' :
                        signal.type === 'bearish' ? 'bg-red-500' : 'bg-gray-400'
                      }`}>
                        {signal.ticker.slice(0, 1)}
                      </div>
                      <div>
                        <div className="font-semibold text-gray-900">{signal.ticker}</div>
                        <div className="text-xs text-gray-500">${signal.price.toLocaleString()}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span
                      className={`text-xs font-medium px-3 py-1.5 rounded-full ${
                        signal.type === 'bullish'
                          ? 'bg-green-100 text-green-800 border border-green-200'
                          : signal.type === 'bearish'
                          ? 'bg-red-100 text-red-800 border border-red-200'
                          : 'bg-gray-100 text-gray-800 border border-gray-200'
                      }`}
                    >
                      {signal.type.charAt(0).toUpperCase() + signal.type.slice(1)}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center gap-3">
                      <div className="w-full bg-gray-200 rounded-full h-2 max-w-[100px]">
                        <div
                          className={`h-2 rounded-full ${
                            signal.confidence > 0.7 ? 'bg-green-500' :
                            signal.confidence > 0.5 ? 'bg-yellow-500' : 'bg-red-500'
                          }`}
                          style={{ width: `${signal.confidence * 100}%` }}
                        ></div>
                      </div>
                      <span className="text-xs font-medium text-gray-600">
                        {(signal.confidence * 100).toFixed(1)}%
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                    ${signal.price.toFixed(2)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                    {signal.rsi ? signal.rsi.toFixed(1) : 'N/A'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span
                      className={`inline-flex items-center px-3 py-1 rounded-lg text-sm font-semibold ${
                        signal.action === 'buy' ? 'bg-green-50 text-green-600' :
                        signal.action === 'sell' ? 'bg-red-50 text-red-600' : 'bg-gray-50 text-gray-600'
                      }`}
                    >
                      {signal.action.toUpperCase()}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700 max-w-xs">
                    <div className="truncate" title={signal.reason}>
                      {signal.reason || 'Technical signal generated'}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-500">
                    {new Date(signal.created_at).toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {filteredSignals.length === 0 && (
            <div className="py-12 text-center">
              <p className="text-gray-500">No signals match your filters</p>
              <button
                onClick={() => {
                  setSelectedFilter('All')
                  setTickerSearch('')
                }}
                className="mt-2 text-blue-600 hover:text-blue-700 font-medium"
              >
                Clear filters
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default SignalCenterPage