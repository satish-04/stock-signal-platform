import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api, endpoints, type Position } from '../lib/types'

const PortfolioPage = () => {
  const [sortConfig, setSortConfig] = useState<{ key: keyof Position; direction: 'asc' | 'desc' }>({
    key: 'ticker',
    direction: 'asc'
  })

  const { data: positionsData = [] } = useQuery<Position[]>({
    queryKey: ['positions'],
    queryFn: () => api.get<Position[]>(endpoints.positions),
  })

  const positions = positionsData.length > 0 ? positionsData : [
    { id: 1, ticker: 'AAPL', quantity: 50, avg_price: 172.45, current_price: 175.23, pnl: 138.50, pnl_percent: '+1.6%', status: 'open' as const },
    { id: 2, ticker: 'NVDA', quantity: 25, avg_price: 910.32, current_price: 923.45, pnl: 328.25, pnl_percent: '+1.9%', status: 'open' as const },
    { id: 3, ticker: 'TSLA', quantity: 30, avg_price: 250.12, current_price: 245.67, pnl: -133.50, pnl_percent: '-1.4%', status: 'open' as const },
    { id: 4, ticker: 'AMD', quantity: 40, avg_price: 168.50, current_price: 178.32, pnl: 392.80, pnl_percent: '+5.8%', status: 'open' as const },
    { id: 5, ticker: 'META', quantity: 15, avg_price: 475.23, current_price: 485.67, pnl: 156.60, pnl_percent: '+2.2%', status: 'open' as const },
  ]

  // Calculate portfolio totals
  const totalValue = positions.reduce((sum, p) => sum + (p.current_price || 0) * p.quantity, 0)
  const dayPnl = positions.reduce((sum, p) => sum + p.pnl, 0)

  // Sort positions
  const sortedPositions = [...positions].sort((a, b) => {
    if (sortConfig === undefined) return 0
    const key = sortConfig.key
    if (a[key] === undefined || b[key] === undefined) return 0
    if (a[key] < b[key]) {
      return sortConfig.direction === 'asc' ? -1 : 1
    }
    if (a[key] > b[key]) {
      return sortConfig.direction === 'asc' ? 1 : -1
    }
    return 0
  })

  const handleSort = (key: keyof Position) => {
    setSortConfig((current) => ({
      key,
      direction: current?.key === key && current.direction === 'asc' ? 'desc' : 'asc'
    }))
  }

  const SortIcon = ({ active, direction }: { active: boolean; direction: 'asc' | 'desc' }) => (
    <span className={`ml-2 ${active ? 'opacity-100' : 'opacity-30'}`}>
      {direction === 'asc' ? (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
        </svg>
      ) : (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      )}
    </span>
  )

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Portfolio</h1>
          <p className="text-gray-500 mt-1">Manage your positions and track performance</p>
        </div>

        <div className="flex gap-3">
          <button className="btn-primary">Add Position</button>
          <button className="btn-secondary">Refresh Data</button>
        </div>
      </div>

      {/* Portfolio Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
          <h3 className="text-sm font-semibold text-blue-800 mb-1">Total Portfolio Value</h3>
          <p className="text-3xl font-bold text-blue-600">${totalValue.toLocaleString()}</p>
          <div className="mt-4">
            <span className="text-xs text-blue-600 font-medium">
              {positions.length} positions
            </span>
          </div>
        </div>

        <div className="card bg-gradient-to-br from-green-50 to-emerald-100 border-green-200">
          <h3 className="text-sm font-semibold text-green-800 mb-1">Today's P&L</h3>
          <p className={`text-3xl font-bold ${dayPnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {dayPnl >= 0 ? '+' : ''}{dayPnl.toLocaleString()}
          </p>
          <div className="mt-4">
            <span className="text-xs text-green-600 font-medium">
              {dayPnl >= 0 ? '+' : ''}{((dayPnl / totalValue) * 100).toFixed(2)}% today
            </span>
          </div>
        </div>

        <div className="card bg-gradient-to-br from-purple-50 to-purple-100 border-purple-200">
          <h3 className="text-sm font-semibold text-purple-800 mb-1">Win Rate</h3>
          <p className="text-3xl font-bold text-purple-600">68%</p>
          <div className="mt-4">
            <span className="text-xs text-purple-600 font-medium">
              32 open positions
            </span>
          </div>
        </div>
      </div>

      {/* Positions Table */}
      <div className="card">
        <div className="mb-6 flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">All Positions</h3>
          <div className="flex items-center gap-2 text-sm text-gray-500">
            <span>Sort by:</span>
            <select
              className="input-base text-sm px-2 py-1"
              value={sortConfig.key}
              onChange={(e) => handleSort(e.target.value as keyof Position)}
            >
              <option value="ticker">Ticker</option>
              <option value="quantity">Quantity</option>
              <option value="pnl">P&L</option>
              <option value="pnl_percent">Return %</option>
            </select>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-200 bg-gray-50">
                <th className="table-header cursor-pointer hover:bg-gray-100 transition-colors" onClick={() => handleSort('ticker')}>
                  <div className="flex items-center">Ticker<SortIcon active={sortConfig.key === 'ticker'} direction={sortConfig.direction} /></div>
                </th>
                <th className="table-header">Quantity</th>
                <th className="table-header cursor-pointer hover:bg-gray-100 transition-colors" onClick={() => handleSort('pnl')}>
                  <div className="flex items-center">Avg Price<SortIcon active={sortConfig.key === 'pnl'} direction={sortConfig.direction} /></div>
                </th>
                <th className="table-header">Current Price</th>
                <th className="table-header cursor-pointer hover:bg-gray-100 transition-colors" onClick={() => handleSort('pnl_percent')}>
                  <div className="flex items-center">Return %<SortIcon active={sortConfig.key === 'pnl_percent'} direction={sortConfig.direction} /></div>
                </th>
                <th className="table-header">Status</th>
                <th className="table-header text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {sortedPositions.map((position) => (
                <tr key={position.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center gap-3">
                      <div
                        className={`w-10 h-10 rounded-lg flex items-center justify-center font-bold text-white ${
                          position.pnl >= 0
                            ? 'bg-green-500'
                            : 'bg-red-500'
                        }`}
                      >
                        {position.ticker.slice(0, 1)}
                      </div>
                      <span className="font-semibold text-gray-900">{position.ticker}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                    {position.quantity}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                    ${position.avg_price.toFixed(2)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                    ${(position.current_price || 0).toFixed(2)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div
                      className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                        position.pnl >= 0
                          ? 'bg-green-100 text-green-800 border border-green-200'
                          : 'bg-red-100 text-red-800 border border-red-200'
                      }`}
                    >
                      {position.pnl_percent}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span
                      className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${
                        position.status === 'open'
                          ? 'bg-green-100 text-green-800 border border-green-200'
                          : 'bg-gray-100 text-gray-800 border border-gray-200'
                      }`}
                    >
                      {position.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right">
                    <div className="flex justify-end gap-2">
                      <button className="btn-secondary text-xs px-2 py-1">Edit</button>
                      <button className="btn-primary text-xs px-2 py-1">Trade</button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {sortedPositions.length === 0 && (
            <div className="py-12 text-center">
              <p className="text-gray-500">No positions yet</p>
              <button className="mt-2 btn-primary">Start Trading</button>
            </div>
          )}
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="card bg-gradient-to-br from-blue-50 to-purple-50 border-blue-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Performance by Sector</h3>
          <div className="space-y-4">
            {[
              { sector: 'Tech', value: 45, color: 'bg-blue-500' },
              { sector: 'Consumer', value: 25, color: 'bg-green-500' },
              { sector: 'Financial', value: 20, color: 'bg-purple-500' },
              { sector: 'Other', value: 10, color: 'bg-gray-500' },
            ].map((item) => (
              <div key={item.sector}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-700 font-medium">{item.sector}</span>
                  <span className="text-blue-600 font-bold">{item.value}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${item.color}`}
                    style={{ width: `${item.value}%` }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="card bg-gradient-to-br from-green-50 to-emerald-50 border-green-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Activity</h3>
          <div className="space-y-3">
            {[
              { action: 'Bought', ticker: 'AAPL', quantity: 50, price: 172.45, date: 'Today' },
              { action: 'Sold', ticker: 'TSLA', quantity: 10, price: 248.90, date: 'Yesterday' },
              { action: 'Bought', ticker: 'AMD', quantity: 40, price: 168.50, date: 'Yesterday' },
            ].map((activity, idx) => (
              <div key={idx} className="flex items-center justify-between p-3 bg-white rounded-lg border">
                <div className="flex items-center gap-3">
                  <span
                    className={`px-2 py-1 rounded-md text-xs font-semibold ${
                      activity.action === 'Bought' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                    }`}
                  >
                    {activity.action}
                  </span>
                  <span className="font-bold text-gray-900">{activity.ticker}</span>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium text-gray-900">{activity.quantity} shares</p>
                  <p className="text-xs text-gray-500">{activity.date}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

export default PortfolioPage