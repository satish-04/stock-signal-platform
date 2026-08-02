import { Link, useLocation } from 'react-router-dom'

interface SidebarProps {
  isOpen: boolean
  setIsOpen: (open: boolean) => void
}

const Sidebar = ({ isOpen, setIsOpen }: SidebarProps) => {
  const location = useLocation()

  const menuItems = [
    { path: '/dashboard', label: 'Dashboard', icon: '📊' },
    { path: '/signals', label: 'Signal Center', icon: '📈' },
    { path: '/options', label: 'Option Chain', icon: '📊' },
    { path: '/scanner', label: 'Market Scanner', icon: '🔍' },
    { path: '/portfolio', label: 'Portfolio', icon: '💼' },
  ]

  return (
    <>
      {/* Mobile overlay with fade */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-20 lg:hidden backdrop-blur-sm transition-all duration-300"
          onClick={() => setIsOpen(false)}
        />
      )}
      
      {/* Sidebar */}
      <aside
        className={`fixed lg:static inset-y-0 left-0 z-30 w-72 bg-gradient-to-br from-gray-900 via-gray-800 to-black text-white transition-transform duration-300 shadow-2xl ${
          isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        }`}
      >
        {/* Brand Header */}
        <div className="p-6 border-b border-gray-700/50 bg-gradient-to-r from-blue-900 via-purple-900 to-indigo-900">
          <div className="flex items-center gap-3 mb-2">
            {/* Custom Logo SVG */}
            <div className="relative">
              <div className="w-12 h-12 bg-gradient-to-br from-blue-500 via-purple-500 to-pink-500 rounded-2xl flex items-center justify-center shadow-lg">
                <svg
                  className="w-7 h-7 text-white"
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
              {/* Animated ring */}
              <div className="absolute inset-0 rounded-2xl border-2 border-blue-500/30 animate-pulse"></div>
            </div>
            
            <div className="flex-1">
              <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent tracking-wide">
                StockSignalAI
              </h1>
              <div className="flex items-center gap-2 mt-1">
                <span className="w-1.5 h-1.5 bg-green-400 rounded-full animate-pulse"></span>
                <p className="text-xs text-gray-400 font-medium">AI Trading Platform</p>
              </div>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="mt-6 px-4 space-y-2">
          {menuItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 group ${
                location.pathname === item.path
                  ? 'bg-gradient-to-r from-blue-600 via-purple-600 to-indigo-600 text-white shadow-lg transform scale-[1.02]'
                  : 'text-gray-300 hover:bg-gray-800/50 hover:text-white'
              }`}
            >
              <div className={`relative ${
                location.pathname === item.path ? 'text-white' : ''
              }`}>
                <span className="text-xl transition-transform duration-200 group-hover:scale-110">
                  {item.icon}
                </span>
                {location.pathname === item.path && (
                  <div className="absolute inset-0 bg-white/20 rounded-xl"></div>
                )}
              </div>
              <span className="font-medium tracking-wide">{item.label}</span>
              {location.pathname === item.path && (
                <div className="ml-auto w-1.5 h-6 bg-gradient-to-b from-blue-400 via-purple-400 to-pink-400 rounded-full"></div>
              )}
            </Link>
          ))}
        </nav>

        {/* Account Status Card */}
        <div className="absolute bottom-0 w-full p-6 border-t border-gray-700/50 bg-gradient-to-b from-black/30 to-transparent backdrop-blur-sm">
          <div className="bg-gradient-to-br from-blue-900/30 to-purple-900/30 rounded-xl p-4 border border-blue-800/30 shadow-lg">
            <div className="flex items-center justify-between mb-4">
              <span className="text-xs font-semibold text-blue-400 uppercase tracking-wider">Account Status</span>
              <div className="flex items-center gap-1.5 bg-green-900/30 px-2 py-1 rounded-full border border-green-800/50">
                <span className="w-1.5 h-1.5 bg-green-400 rounded-full animate-pulse"></span>
                <span className="text-[10px] text-green-300 font-medium">Connected</span>
              </div>
            </div>
            
            <div className="space-y-3">
              <div className="flex justify-between items-center text-xs">
                <span className="text-gray-400">Total Equity</span>
                <div className="flex items-center gap-1.5">
                  <svg
                    className="w-3 h-3 text-green-400"
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
                  <span className="font-bold text-green-400">$100,000.00</span>
                </div>
              </div>
              
              <div className="flex justify-between items-center text-xs">
                <span className="text-gray-400">Day P&L</span>
                <div className="flex items-center gap-1.5">
                  <svg
                    className="w-3 h-3 text-green-400"
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
                  <span className="font-bold text-green-400">+2.9%</span>
                </div>
              </div>
              
              {/* Progress Bar */}
              <div className="pt-3">
                <div className="flex justify-between text-xs mb-2">
                  <span className="text-gray-400">Portfolio Utilization</span>
                  <span className="font-semibold text-blue-400">32%</span>
                </div>
                <div className="w-full bg-gray-700/50 rounded-full h-1.5">
                  <div className="h-1.5 rounded-full bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500" style={{ width: '32%' }}></div>
                </div>
              </div>
            </div>

            {/* Account Type Badge */}
            <div className="mt-4 pt-4 border-t border-blue-800/30">
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-400">Account Type</span>
                <div className="px-2 py-1 bg-gradient-to-r from-blue-600 to-purple-600 rounded-md">
                  <span className="text-white font-semibold">Paper Trading</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </aside>
    </>
  )
}

export default Sidebar