import {
  ActivityIcon,
  BriefcaseIcon,
  CandlestickChartIcon,
  LayersIcon,
  LayoutDashboardIcon,
  ListChecksIcon,
  ServerIcon,
  ShieldCheckIcon,
  WorkflowIcon,
  type LucideIcon,
} from 'lucide-react'

export interface NavItem {
  to: string
  label: string
  icon: LucideIcon
  mobilePrimary?: boolean
}

export const NAV_ITEMS: NavItem[] = [
  { to: '/', label: 'Overview', icon: LayoutDashboardIcon, mobilePrimary: true },
  { to: '/signals', label: 'Signals', icon: ActivityIcon, mobilePrimary: true },
  { to: '/positions', label: 'Positions', icon: BriefcaseIcon, mobilePrimary: true },
  { to: '/market', label: 'Market', icon: CandlestickChartIcon, mobilePrimary: true },
  { to: '/options', label: 'Options', icon: LayersIcon },
  { to: '/risk', label: 'Risk & AI', icon: ShieldCheckIcon },
  { to: '/orders', label: 'Orders', icon: ListChecksIcon },
  { to: '/workflows', label: 'Workflows', icon: WorkflowIcon },
  { to: '/jobs', label: 'Jobs', icon: ServerIcon },
]
