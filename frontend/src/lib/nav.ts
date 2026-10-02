import {
  ActivityIcon,
  BriefcaseIcon,
  CandlestickChartIcon,
  FileTextIcon,
  FlaskConicalIcon,
  LayersIcon,
  LayoutDashboardIcon,
  ListChecksIcon,
  RadarIcon,
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
  { to: '/scanner', label: 'Scanner', icon: RadarIcon },
  { to: '/research', label: 'Research', icon: FileTextIcon },
  { to: '/quant', label: 'Quant lab', icon: FlaskConicalIcon },
  { to: '/risk', label: 'Risk & AI', icon: ShieldCheckIcon },
  { to: '/orders', label: 'Orders', icon: ListChecksIcon },
  { to: '/workflows', label: 'Workflows', icon: WorkflowIcon },
  { to: '/jobs', label: 'Jobs', icon: ServerIcon },
]
