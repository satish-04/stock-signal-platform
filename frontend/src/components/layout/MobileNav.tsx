import { MoreHorizontalIcon } from 'lucide-react'
import { NavLink, useLocation } from 'react-router-dom'
import { cn } from '@/lib/cn'
import { NAV_ITEMS } from '@/lib/nav'
import { Drawer } from '@/components/ui/Drawer'

const PRIMARY_ITEMS = NAV_ITEMS.filter((item) => item.mobilePrimary)
const OVERFLOW_ITEMS = NAV_ITEMS.filter((item) => !item.mobilePrimary)

export function BottomTabBar({ onMore }: { onMore: () => void }) {
  const location = useLocation()
  const isOverflowActive = OVERFLOW_ITEMS.some((item) => item.to === location.pathname)

  return (
    <nav className="flex h-16 items-stretch border-t border-border bg-surface md:hidden">
      {PRIMARY_ITEMS.map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          end={item.to === '/'}
          className={({ isActive }) =>
            cn(
              'flex flex-1 flex-col items-center justify-center gap-0.5 text-[11px] font-medium',
              isActive ? 'text-series-1' : 'text-text-secondary',
            )
          }
        >
          <item.icon className="h-5 w-5" aria-hidden="true" />
          {item.label}
        </NavLink>
      ))}
      <button
        onClick={onMore}
        className={cn(
          'flex flex-1 flex-col items-center justify-center gap-0.5 text-[11px] font-medium',
          isOverflowActive ? 'text-series-1' : 'text-text-secondary',
        )}
      >
        <MoreHorizontalIcon className="h-5 w-5" aria-hidden="true" />
        More
      </button>
    </nav>
  )
}

export function MobileNavDrawer({ open, onClose }: { open: boolean; onClose: () => void }) {
  return (
    <Drawer open={open} onClose={onClose} title="Navigate" side="left">
      <nav className="space-y-0.5">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            onClick={onClose}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 rounded-md px-2.5 py-2.5 text-sm font-medium',
                isActive ? 'bg-series-1/10 text-series-1' : 'text-text-secondary hover:bg-hover hover:text-text-primary',
              )
            }
          >
            <item.icon className="h-4 w-4 shrink-0" aria-hidden="true" />
            {item.label}
          </NavLink>
        ))}
      </nav>
    </Drawer>
  )
}
