import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useState } from 'react'

// Pages
import DashboardPage from './pages/DashboardPage'
import SignalCenterPage from './pages/SignalCenterPage'
import OptionChainPage from './pages/OptionChainPage'
import MarketScannerPage from './pages/MarketScannerPage'
import PortfolioPage from './pages/PortfolioPage'

// Components
import Navbar from './components/Navbar'
import Sidebar from './components/Sidebar'

// Create query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60 * 1000,
    },
    mutations: {
      retry: 1,
    },
  },
})

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false)

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div className="app-container flex min-h-screen bg-gray-50">
          {/* Sidebar */}
          <Sidebar isOpen={sidebarOpen} setIsOpen={setSidebarOpen} />
          
          {/* Main Content */}
          <div className="flex-1 flex flex-col min-h-screen overflow-hidden">
            <Navbar onMenuClick={() => setSidebarOpen(!sidebarOpen)} />
            
            <main className="flex-1 overflow-y-auto p-6 content-wrapper">
              <Routes>
                <Route path="/" element={<DashboardPage />} />
                <Route path="/dashboard" element={<DashboardPage />} />
                <Route path="/signals" element={<SignalCenterPage />} />
                <Route path="/options" element={<OptionChainPage />} />
                <Route path="/scanner" element={<MarketScannerPage />} />
                <Route path="/portfolio" element={<PortfolioPage />} />
              </Routes>
            </main>
          </div>
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

export default App
