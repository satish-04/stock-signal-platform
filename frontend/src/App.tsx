import { lazy, Suspense } from 'react'
import { createBrowserRouter, RouterProvider } from 'react-router-dom'
import { AppShell } from '@/components/layout/AppShell'
import { Skeleton } from '@/components/ui/Skeleton'

const OverviewPage = lazy(() => import('@/features/overview/OverviewPage').then((m) => ({ default: m.OverviewPage })))
const SignalsPage = lazy(() => import('@/features/signals/SignalsPage').then((m) => ({ default: m.SignalsPage })))
const PositionsPage = lazy(() => import('@/features/positions/PositionsPage').then((m) => ({ default: m.PositionsPage })))
const OptionsPage = lazy(() => import('@/features/options/OptionsPage').then((m) => ({ default: m.OptionsPage })))
const MarketPage = lazy(() => import('@/features/market/MarketPage').then((m) => ({ default: m.MarketPage })))
const RiskPage = lazy(() => import('@/features/risk/RiskPage').then((m) => ({ default: m.RiskPage })))
const OrdersPage = lazy(() => import('@/features/orders/OrdersPage').then((m) => ({ default: m.OrdersPage })))
const WorkflowsPage = lazy(() => import('@/features/workflows/WorkflowsPage').then((m) => ({ default: m.WorkflowsPage })))
const JobsPage = lazy(() => import('@/features/jobs/JobsPage').then((m) => ({ default: m.JobsPage })))

function withSuspense(element: React.ReactNode) {
  return <Suspense fallback={<Skeleton className="h-64 w-full" />}>{element}</Suspense>
}

const router = createBrowserRouter([
  {
    element: <AppShell />,
    children: [
      { path: '/', element: withSuspense(<OverviewPage />) },
      { path: '/signals', element: withSuspense(<SignalsPage />) },
      { path: '/positions', element: withSuspense(<PositionsPage />) },
      { path: '/options', element: withSuspense(<OptionsPage />) },
      { path: '/market', element: withSuspense(<MarketPage />) },
      { path: '/risk', element: withSuspense(<RiskPage />) },
      { path: '/orders', element: withSuspense(<OrdersPage />) },
      { path: '/workflows', element: withSuspense(<WorkflowsPage />) },
      { path: '/jobs', element: withSuspense(<JobsPage />) },
    ],
  },
])

function App() {
  return <RouterProvider router={router} />
}

export default App
