import { useQuery } from '@tanstack/react-query'
import { api, endpoints, mockData, type PortfolioSummary, type Signal } from '../lib/types'
import { Link } from 'react-router-dom'

const DashboardPage = () => {
  const { data: portfolioData } = useQuery<PortfolioSummary>({
    queryKey: ['dashboard'],
    queryFn: () => api.get<PortfolioSummary>(endpoints.portfolio),
  })

  const portfolio = portfolioData || mockData

  const { data: signals = [] } = useQuery<Signal[]>({
    queryKey: ['signals', 'all'],
    queryFn: () => api.get<Signal[]>(endpoints.signals),
  })

  // Calculate summary metrics
  const totalValue = portfolio.total_value || 152489.37
  const dayPnl = portfolio.day_pnl || 3456.12
  const dayPnlPercent = (dayPnl / totalValue) * 100

  // Get today's date
  const today = new Date().toLocaleDateString('en-US', { 
    weekday: 'long', 
    year: 'numeric', 
    month: 'long', 
    day: 'numeric' 
  })

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
            <span className="w-12 h-12 bg-gradient-to-br from-blue-500 via-purple-600 to-pink-600 rounded-xl flex items-center justify-center text-white shadow-lg">
              <svg
                className="w-6 h-6"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                />
              </svg>
            </span>
            Dashboard
          </h1>
          <div className="flex items-center gap-2 mt-2 text-gray-500">
            <span>{today}</span>
            <span className="w-1 h-1 bg-gray-300 rounded-full"></span>
            <div className="flex items-center gap-1">
              <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
              <span className="text-sm font-medium">Market Open</span>
            </div>
          </div>
        </div>
        
        <div className="flex gap-2">
          <Link to="/signals" className="btn-primary flex items-center gap-2">
            <svg
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"
              />
            </svg>
            View Signals
          </Link>
          <button className="btn-secondary flex items-center gap-2">
            <svg
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              />
            </svg>
            Refresh
          </button>
        </div>
      </div>

      {/* Key Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Total Equity Card */}
        <div className="card relative overflow-hidden group bg-gradient-to-br from-white to-blue-50/30">
          <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
            <div className="w-16 h-16 bg-gradient-to-br from-blue-400 to-purple-500 rounded-full"></div>
          </div>
          
          <div className="relative z-10">
            <div className="flex items-center gap-2 mb-3">
              <span className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center text-white shadow-md">
                <svg
                  className="w-4 h-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
              </span>
              <h3 className="text-sm font-semibold text-gray-700">Total Equity</h3>
            </div>
            
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-bold text-gray-900 tracking-tight">
                ${totalValue.toLocaleString()}
              </span>
            </div>
            
            <div className="mt-4 flex items-center gap-2">
              <span
                className={`px-3 py-1 rounded-full text-xs font-semibold ${
                  dayPnl >= 0
                    ? 'bg-green-100 text-green-700 border border-green-200'
                    : 'bg-red-100 text-red-700 border border-red-200'
                }`}
              >
                {dayPnl >= 0 ? '+' : ''}{dayPnlPercent.toFixed(2)}%
              </span>
              <span className="text-xs text-gray-500 font-medium">Today's P&L</span>
            </div>

            <div className="mt-4">
              <div className="flex justify-between text-xs mb-1.5">
                <span className="text-gray-500 font-medium">Equity Growth</span>
                <span className="text-blue-600 font-semibold">+12.5%</span>
              </div>
              <div className="w-full bg-gray-100 rounded-full h-1.5">
                <div
                  className="h-1.5 rounded-full bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500"
                  style={{ width: '75%' }}
                ></div>
              </div>
            </div>
          </div>
        </div>

        {/* Day P&L Card */}
        <div className="card relative overflow-hidden group bg-gradient-to-br from-white to-green-50/30">
          <div className={`absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity ${
            dayPnl >= 0 ? 'text-green-500' : 'text-red-500'
          }`}>
            <div className="w-16 h-16 bg-gradient-to-br from-green-400 to-emerald-500 rounded-full"></div>
          </div>

          <div className="relative z-10">
            <div className="flex items-center gap-2 mb-3">
              <span className={`w-8 h-8 rounded-lg flex items-center justify-center text-white shadow-md ${
                dayPnl >= 0 ? 'bg-gradient-to-br from-green-500 to-emerald-600' : 'bg-gradient-to-br from-red-500 to-orange-600'
              }`}>
                <svg
                  className="w-4 h-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"
                  />
                </svg>
              </span>
              <h3 className="text-sm font-semibold text-gray-700">Day P&L</h3>
            </div>

            <div className="flex items-baseline gap-2">
              <span
                className={`text-3xl font-bold ${
                  dayPnl >= 0 ? 'text-green-600' : 'text-red-600'
                }`}
              >
                {dayPnl >= 0 ? '+' : ''}{dayPnl.toLocaleString()}
              </span>
            </div>

            <div className="mt-4">
              <div className="flex justify-between text-xs mb-1.5">
                <span className="text-gray-500 font-medium">Performance</span>
                <span className={dayPnl >= 0 ? 'text-green-600 font-semibold' : 'text-red-600 font-semibold'}>
                  {dayPnl >= 0 ? 'Positive' : 'Negative'}
                </span>
              </div>
              <div className="w-full bg-gray-100 rounded-full h-2">
                <div
                  className={`h-2 rounded-full ${
                    dayPnl >= 0 ? 'bg-gradient-to-r from-green-500 to-emerald-600' : 'bg-gradient-to-r from-red-500 to-orange-600'
                  }`}
                  style={{ width: `${Math.abs(dayPnlPercent) * 10}%` }}
                ></div>
              </div>
            </div>
          </div>
        </div>

        {/* Open Positions Card */}
        <div className="card relative overflow-hidden group bg-gradient-to-br from-white to-purple-50/30">
          <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
            <div className="w-16 h-16 bg-gradient-to-br from-purple-400 to-indigo-500 rounded-full"></div>
          </div>

          <div className="relative z-10">
            <div className="flex items-center gap-2 mb-3">
              <span className="w-8 h-8 bg-gradient-to-br from-purple-500 to-indigo-600 rounded-lg flex items-center justify-center text-white shadow-md">
                <svg
                  className="w-4 h-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
                  />
                </svg>
              </span>
              <h3 className="text-sm font-semibold text-gray-700">Open Positions</h3>
            </div>

            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-bold text-gray-900 tracking-tight">{portfolio.open_positions || 12}</span>
              <span className="text-sm text-gray-500 font-medium">active</span>
            </div>

            <div className="mt-6">
              <div className="flex justify-between text-sm mb-3 p-2 bg-gray-50 rounded-lg border border-gray-100">
                <div className="flex items-center gap-2 text-gray-700 font-medium">
                  <span>📊</span>
                  <span>Total Trades</span>
                </div>
                <span className="font-bold text-gray-900">{portfolio.total_trades || 47}</span>
              </div>

              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-600 font-medium">Win Rate</span>
                <div className="flex items-center gap-1.5">
                  <div className="w-full bg-gray-200 rounded-full h-1.5 max-w-[80px]">
                    <div
                      className="h-1.5 rounded-full bg-gradient-to-r from-green-500 to-emerald-600"
                      style={{ width: '68%' }}
                    ></div>
                  </div>
                  <span className="font-bold text-green-600">{portfolio.win_rate || '68%'}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Performance Card */}
        <div className="card relative overflow-hidden group bg-gradient-to-br from-white to-orange-50/30">
          <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
            <div className="w-16 h-16 bg-gradient-to-br from-orange-400 to-red-500 rounded-full"></div>
          </div>

          <div className="relative z-10">
            <div className="flex items-center gap-2 mb-3">
              <span className="w-8 h-8 bg-gradient-to-br from-orange-500 to-red-600 rounded-lg flex items-center justify-center text-white shadow-md">
                <svg
                  className="w-4 h-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                  />
                </svg>
              </span>
              <h3 className="text-sm font-semibold text-gray-700">Performance</h3>
            </div>

            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-bold text-gray-900 tracking-tight">+12.5%</span>
              <span className="text-sm text-gray-500 font-medium">YTD Return</span>
            </div>

            <div className="mt-4 space-y-3">
              <div className="flex items-center justify-between text-sm p-2 bg-gray-50 rounded-lg border border-gray-100">
                <div className="flex items-center gap-2 text-gray-700 font-medium">
                  <span>📈</span>
                  <span>Benchmark</span>
                </div>
                <span className="font-semibold text-green-600">+8.2%</span>
              </div>

              <div className="flex items-center justify-between text-sm p-2 bg-gray-50 rounded-lg border border-gray-100">
                <div className="flex items-center gap-2 text-gray-700 font-medium">
                  <span>🏆</span>
                  <span>Outperformance</span>
                </div>
                <span className="font-semibold text-blue-600">+4.3%</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Signals Table */}
        <div className="lg:col-span-2 card bg-white shadow-sm border-gray-200">
          <div className="flex items-center justify-between mb-6 pb-4 border-b border-gray-200">
            <div className="flex items-center gap-3">
              <span className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center text-white shadow-lg">
                📈
              </span>
              <h3 className="text-lg font-semibold text-gray-900">Recent Signals</h3>
            </div>

            <Link to="/signals" className="flex items-center gap-1 text-sm font-medium text-blue-600 hover:text-blue-700 transition-colors">
              View All
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 5l7-7m0 0l7 7m-7-7v18"
                />
              </svg>
            </Link>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200 bg-gray-50/50">
                  <th className="table-header">Ticker</th>
                  <th className="table-header">Type</th>
                  <th className="table-header">Confidence</th>
                  <th className="table-header">Action</th>
                  <th className="table-header text-right">Time</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {signals.length > 0 ? (
                  signals.slice(0, 5).map((signal) => (
                    <tr key={signal.id} className="hover:bg-gray-50 transition-colors group">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center gap-3">
                          <div className={`w-10 h-10 rounded-xl flex items-center justify-center font-bold text-white ${
                            signal.type === 'bullish'
                              ? 'bg-gradient-to-br from-green-500 to-emerald-600'
                              : signal.type === 'bearish'
                              ? 'bg-gradient-to-br from-red-500 to-orange-600'
                              : 'bg-gray-500'
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
                        <div
                          className={`inline-flex items-center px-3 py-1.5 rounded-full text-xs font-semibold ${
                            signal.type === 'bullish'
                              ? 'bg-green-100 text-green-700 border border-green-200'
                              : signal.type === 'bearish'
                              ? 'bg-red-100 text-red-700 border border-red-200'
                              : 'bg-gray-100 text-gray-700 border border-gray-200'
                          }`}
                        >
                          {signal.type.charAt(0).toUpperCase() + signal.type.slice(1)}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center gap-3">
                          <div className="w-full bg-gray-200 rounded-full h-1.5 max-w-[100px]">
                            <div
                              className={`h-1.5 rounded-full ${
                                signal.confidence > 0.7
                                  ? 'bg-gradient-to-r from-green-500 to-emerald-600'
                                  : signal.confidence > 0.5
                                  ? 'bg-gradient-to-r from-yellow-400 to-orange-500'
                                  : 'bg-gradient-to-r from-red-500 to-orange-600'
                              }`}
                              style={{ width: `${signal.confidence * 100}%` }}
                            ></div>
                          </div>
                          <span className="text-xs font-semibold text-gray-600">
                            {(signal.confidence * 100).toFixed(1)}%
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`inline-flex items-center px-3 py-1 rounded-lg text-sm font-bold ${
                            signal.action === 'buy'
                              ? 'bg-green-50 text-green-700 border border-green-200'
                              : signal.action === 'sell'
                              ? 'bg-red-50 text-red-700 border border-red-200'
                              : 'bg-gray-50 text-gray-700 border border-gray-200'
                          }`}
                        >
                          {signal.action.toUpperCase()}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium text-gray-500">
                        {new Date(signal.created_at).toLocaleTimeString([], {
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={5} className="px-6 py-12 text-center text-gray-500">
                      No signals generated yet
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Quick Stats / Portfolio Overview */}
        <div className="card bg-white shadow-sm border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <svg
              className="w-5 h-5 text-blue-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
              />
            </svg>
            Quick Stats
          </h3>

          <div className="space-y-4">
            <div className="flex items-center justify-between p-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl border border-blue-100 shadow-sm hover:shadow-md transition-shadow">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center text-white">
                  <svg
                    className="w-5 h-5"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                    />
                  </svg>
                </div>
                <div>
                  <p className="text-xs text-blue-700 font-medium">Total Trades</p>
                  <p className="text-lg font-bold text-gray-900">{portfolio.total_trades || 47}</p>
                </div>
              </div>
            </div>

            <div className="flex items-center justify-between p-4 bg-gradient-to-r from-green-50 to-emerald-50 rounded-xl border border-green-100 shadow-sm hover:shadow-md transition-shadow">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-gradient-to-br from-green-500 to-emerald-600 rounded-lg flex items-center justify-center text-white">
                  <svg
                    className="w-5 h-5"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  </svg>
                </div>
                <div>
                  <p className="text-xs text-green-700 font-medium">Win Rate</p>
                  <p className="text-lg font-bold text-gray-900">{portfolio.win_rate || '68%'}</p>
                </div>
              </div>
            </div>

            <div className="flex items-center justify-between p-4 bg-gradient-to-r from-purple-50 to-indigo-50 rounded-xl border border-purple-100 shadow-sm hover:shadow-md transition-shadow">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-indigo-600 rounded-lg flex items-center justify-center text-white">
                  <svg
                    className="w-5 h-5"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"
                    />
                  </svg>
                </div>
                <div>
                  <p className="text-xs text-purple-700 font-medium">Total Return</p>
                  <p className="text-lg font-bold text-gray-900">+12.5%</p>
                </div>
              </div>
            </div>

            <div className="flex items-center justify-between p-4 bg-gradient-to-r from-orange-50 to-red-50 rounded-xl border border-orange-100 shadow-sm hover:shadow-md transition-shadow">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-gradient-to-br from-orange-500 to-red-600 rounded-lg flex items-center justify-center text-white">
                  <svg
                    className="w-5 h-5"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
                    />
                  </svg>
                </div>
                <div>
                  <p className="text-xs text-orange-700 font-medium">Winners</p>
                  <p className="text-lg font-bold text-gray-900">32</p>
                </div>
              </div>
            </div>
          </div>

          {/* Trading Mode Indicator */}
          <div className="mt-6 pt-6 border-t border-gray-200">
            <div className="flex items-center gap-3 p-4 bg-blue-50 rounded-xl border border-blue-100">
              <div className="flex items-center gap-2 px-3 py-2 bg-blue-600 rounded-lg shadow-sm">
                <svg
                  className="w-4 h-4 text-white"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
                  />
                </svg>
                <span className="text-xs font-bold text-white">Paper Trading</span>
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-900">Real-time market data</p>
                <div className="flex items-center gap-1 mt-1">
                  <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
                  <p className="text-xs text-green-600 font-medium">Connected</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Portfolio Overview */}
        <div className="card bg-white shadow-sm border-gray-200">
          <div className="flex items-center justify-between mb-6 pb-4 border-b border-gray-200">
            <div className="flex items-center gap-3">
              <span className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center text-white shadow-lg">
                💼
              </span>
              <h3 className="text-lg font-semibold text-gray-900">Portfolio Overview</h3>
            </div>

            <Link to="/portfolio" className="flex items-center gap-1 text-sm font-medium text-blue-600 hover:text-blue-700 transition-colors">
              View All Positions
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 5l7-7m0 0l7 7m-7-7v18"
                />
              </svg>
            </Link>
          </div>

          <div className="space-y-4">
            {[
              {
                ticker: 'AAPL',
                quantity: 50,
                avg_price: 172.45,
                current_price: 175.23,
                pnl: 138.50,
                pnl_percent: '+1.6%',
                status: 'open',
              },
              {
                ticker: 'NVDA',
                quantity: 25,
                avg_price: 910.32,
                current_price: 923.45,
                pnl: 328.25,
                pnl_percent: '+1.9%',
                status: 'open',
              },
              {
                ticker: 'TSLA',
                quantity: 30,
                avg_price: 250.12,
                current_price: 245.67,
                pnl: -133.50,
                pnl_percent: '-1.4%',
                status: 'open',
              },
            ].map((position, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between p-4 bg-gray-50 rounded-xl hover:bg-white hover:shadow-md transition-all duration-200 border border-transparent hover:border-gray-200 group"
              >
                <div className="flex items-center gap-4">
                  <div className={`w-12 h-12 rounded-xl flex items-center justify-center text-lg font-bold text-white ${
                    position.pnl >= 0
                      ? 'bg-gradient-to-br from-green-500 to-emerald-600 shadow-lg'
                      : 'bg-gradient-to-br from-red-500 to-orange-600 shadow-lg'
                  }`}>
                    {position.ticker.slice(0, 1)}
                  </div>
                  <div>
                    <h4 className="font-semibold text-gray-900">{position.ticker}</h4>
                    <p className="text-sm text-gray-500">
                      {position.quantity} shares @ ${position.avg_price.toFixed(2)}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-6">
                  <div className="text-right hidden md:block">
                    <p className="font-semibold text-gray-900">${position.current_price.toFixed(2)}</p>
                    <p className="text-xs text-gray-500">Current Price</p>
                  </div>

                  <div className="text-right">
                    <p
                      className={`font-bold ${
                        position.pnl >= 0 ? 'text-green-600' : 'text-red-600'
                      }`}
                    >
                      {position.pnl_percent}
                    </p>
                    <p className="text-xs text-gray-500">
                      {position.pnl >= 0 ? '+' : ''}${position.pnl.toFixed(2)} P&L
                    </p>
                  </div>

                  <button className="btn-secondary text-sm px-3 py-1.5 group-hover:bg-blue-600 group-hover:text-white transition-colors">
                    Trade
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Market Snapshot */}
        <div className="card bg-white shadow-sm border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <svg
              className="w-5 h-5 text-blue-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"
              />
            </svg>
            Market Snapshot
          </h3>

          <div className="space-y-3">
            {[
              {
                ticker: 'AAPL',
                price: 175.23,
                change: '+1.2%',
                volume: '45M',
                signal: 'bullish',
              },
              {
                ticker: 'NVDA',
                price: 923.45,
                change: '-0.8%',
                volume: '32M',
                signal: 'bearish',
              },
              {
                ticker: 'TSLA',
                price: 245.67,
                change: '+2.1%',
                volume: '28M',
                signal: 'bullish',
              },
            ].map((stock, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between p-3 hover:bg-gray-50 rounded-xl transition-colors cursor-pointer group border border-transparent hover:border-gray-200"
              >
                <div className="flex items-center gap-3">
                  <span className="font-bold text-gray-900">{stock.ticker}</span>
                  <span className="text-sm text-gray-500">${stock.price.toFixed(2)}</span>
                </div>

                <div className="flex items-center gap-4">
                  <div className="text-right hidden sm:block">
                    <span
                      className={`font-semibold ${
                        stock.change.startsWith('+') ? 'text-green-600' : 'text-red-600'
                      }`}
                    >
                      {stock.change}
                    </span>
                  </div>

                  <div className="w-24 h-1.5 bg-gray-100 rounded-full hidden sm:block">
                    <div
                      className={`h-1.5 rounded-full ${
                        stock.signal === 'bullish'
                          ? 'bg-gradient-to-r from-green-500 to-emerald-600'
                          : stock.signal === 'bearish'
                          ? 'bg-gradient-to-r from-red-500 to-orange-600'
                          : 'bg-gray-400'
                      }`}
                      style={{ width: `${Math.random() * 60 + 20}%` }}
                    ></div>
                  </div>

                  <button className="btn-secondary text-xs px-2 py-1 group-hover:bg-blue-50 group-hover:text-blue-600 transition-colors">
                    Details
                  </button>
                </div>
              </div>
            ))}
          </div>

          <Link
            to="/scanner"
            className="block mt-4 text-center btn-primary py-2.5 hover:shadow-lg transition-shadow"
          >
            View Full Market Scanner
          </Link>
        </div>
      </div>
    </div>
  )
}

export default DashboardPage