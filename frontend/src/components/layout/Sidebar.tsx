import { ChevronsLeftIcon, ChevronsRightIcon } from 'lucide-react'
import { NavLink } from 'react-router-dom'
import { cn } from '@/lib/cn'
import { NAV_ITEMS } from '@/lib/nav'
import { useUIStore } from '@/store/uiStore'

export function Sidebar() {
  const collapsed = useUIStore((s) => s.sidebarCollapsed)
  const toggleSidebar = useUIStore((s) => s.toggleSidebar)

  return (
    <aside
      className={cn(
        'hidden shrink-0 flex-col border-r border-border bg-surface transition-[width] duration-150 md:flex',
        collapsed ? 'w-16' : 'w-56',
      )}
    >
      <div className="flex h-14 items-center gap-2 border-b border-border px-4">
        <div className="h-6 w-6 shrink-0 rounded-md bg-series-1" aria-hidden="true" />
        {!collapsed && <span className="truncate text-sm font-semibold text-text-primary">Signal Platform</span>}
      </div>

      <nav className="scroll-thin flex-1 space-y-0.5 overflow-y-auto p-2">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 rounded-md px-2.5 py-2 text-sm font-medium transition-colors',
                isActive ? 'bg-series-1/10 text-series-1' : 'text-text-secondary hover:bg-hover hover:text-text-primary',
              )
            }
            title={collapsed ? item.label : undefined}
          >
            <item.icon className="h-4 w-4 shrink-0" aria-hidden="true" />
            {!collapsed && <span className="truncate">{item.label}</span>}
          </NavLink>
        ))}
      </nav>

      <button
        onClick={toggleSidebar}
        className="flex items-center gap-2 border-t border-border px-4 py-3 text-xs text-text-secondary hover:bg-hover hover:text-text-primary"
      >
        {collapsed ? <ChevronsRightIcon className="h-4 w-4" /> : <ChevronsLeftIcon className="h-4 w-4" />}
        {!collapsed && 'Collapse'}
      </button>
    </aside>
  )
}
