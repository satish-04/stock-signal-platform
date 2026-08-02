import { Link, useLocation } from 'react-router-dom'

interface NavbarProps {
  onMenuClick: () => void
}

const Navbar = ({ onMenuClick }: NavbarProps) => {
  const location = useLocation()

  return (
    <header className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between sticky top-0 z-10 shadow-sm">
      {/* Left: Menu + Logo */}
      <div className="flex items-center gap-4">
        <button
          onClick={onMenuClick}
          className="lg:hidden p-2 rounded-lg hover:bg-gray-100 transition-colors"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-6 w-6 text-gray-700"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4 6h16M4 12h16M4 18h16"
            />
          </svg>
        </button>

        {/* Logo in Navbar */}
        <Link to="/dashboard" className="hidden lg:flex items-center gap-2">
          <div className="w-8 h-8 bg-gradient-to-br from-blue-500 via-purple-500 to-pink-500 rounded-lg flex items-center justify-center shadow-md">
            <svg
              className="w-5 h-5 text-white"
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
          <span className="text-xl font-bold bg-gradient-to-r from-blue-600 to-purple-700 bg-clip-text text-transparent">
            StockSignalAI
          </span>
        </Link>

        <div className="hidden lg:block">
          <h2 className="text-xl font-semibold text-gray-900">
            {location.pathname === '/dashboard' ? 'Dashboard' : location.pathname.replace('/', '').charAt(0).toUpperCase() + location.pathname.replace('/', '').slice(1)}
          </h2>
        </div>
      </div>

      {/* Right: Account Info & Navigation */}
      <div className="flex items-center gap-6">
        {/* Desktop Navigation */}
        <nav className="hidden lg:flex items-center gap-2 bg-gray-50 rounded-lg p-1">
          {[
            { path: '/dashboard', label: 'Dashboard' },
            { path: '/signals', label: 'Signals' },
            { path: '/options', label: 'Options' },
            { path: '/scanner', label: 'Scanner' },
            { path: '/portfolio', label: 'Portfolio' },
          ].map((link) => (
            <Link
              key={link.path}
              to={link.path}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-all duration-200 ${
                location.pathname === link.path
                  ? 'bg-white text-blue-700 shadow-md'
                  : 'text-gray-600 hover:bg-white/50 hover:text-blue-600'
              }`}
            >
              {link.label}
            </Link>
          ))}
        </nav>

        {/* Account Info */}
        <div className="flex items-center gap-4">
          {/* Balance Card */}
          <div className="hidden lg:flex items-center gap-2 bg-gradient-to-r from-green-50 to-emerald-50 px-4 py-2 rounded-lg border border-green-100 shadow-sm">
            <div className="text-xs text-gray-600 font-medium">Balance:</div>
            <div className="flex items-center gap-2">
              <span className="text-sm font-bold text-green-700">$100,000.00</span>
              <div className="flex items-center gap-1 px-2 py-0.5 bg-green-100 rounded-full border border-green-200">
                <svg
                  className="w-3 h-3 text-green-600"
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
                <span className="text-[10px] font-medium text-green-700">+2.9%</span>
              </div>
            </div>
          </div>

          {/* User Profile */}
          <div className="flex items-center gap-3">
            {/* User Avatar with Gradient */}
            <button className="relative w-10 h-10 rounded-full overflow-hidden border-2 border-white shadow-lg transition-transform hover:scale-110 focus:outline-none focus:border-blue-400">
              <div className="absolute inset-0 bg-gradient-to-br from-blue-500 via-purple-600 to-pink-500"></div>
              <span className="relative z-10 text-white font-bold text-sm">US</span>
              {/* Notification Dot */}
              <div className="absolute top-0 right-0 w-3 h-3 bg-red-500 rounded-full border-2 border-white"></div>
            </button>

            <div className="hidden lg:flex flex-col items-start">
              <span className="text-xs font-semibold text-gray-900">User Account</span>
              <div className="flex items-center gap-1">
                <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
                <span className="text-[10px] text-gray-500">Paper Trading Active</span>
              </div>
            </div>
          </div>

          {/* Settings Button */}
          <button className="hidden lg:flex w-10 h-10 items-center justify-center rounded-lg bg-gray-50 hover:bg-gray-100 text-gray-600 transition-colors">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-5 w-5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
              />
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
              />
            </svg>
          </button>
        </div>
      </div>
    </header>
  )
}

export default Navbar