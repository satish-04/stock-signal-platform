import { MenuIcon, MoonIcon, SunIcon } from 'lucide-react'
import { useHealth } from '@/api/queries/health'
import { Input } from '@/components/ui/Input'
import { StatusBadge } from '@/components/ui/StatusBadge'
import { applyThemeToDocument, useUIStore } from '@/store/uiStore'

export function TopBar({ onOpenMobileNav }: { onOpenMobileNav: () => void }) {
  const { data: health } = useHealth()
  const theme = useUIStore((s) => s.theme)
  const setTheme = useUIStore((s) => s.setTheme)
  const selectedAccountId = useUIStore((s) => s.selectedAccountId)
  const setSelectedAccountId = useUIStore((s) => s.setSelectedAccountId)

  const toggleTheme = () => {
    const next = theme === 'dark' ? 'light' : 'dark'
    setTheme(next)
    applyThemeToDocument(next)
  }

  return (
    <header className="flex h-14 items-center gap-3 border-b border-border bg-surface px-3 md:px-4">
      <button
        onClick={onOpenMobileNav}
        className="rounded-md p-1.5 text-text-secondary hover:bg-hover md:hidden"
        aria-label="Open navigation"
      >
        <MenuIcon className="h-5 w-5" />
      </button>

      <div className="flex flex-1 items-center gap-3">
        <label className="hidden items-center gap-2 sm:flex">
          <span className="whitespace-nowrap text-xs font-medium text-text-secondary">Account</span>
          <Input
            value={selectedAccountId}
            onChange={(e) => setSelectedAccountId(e.target.value)}
            placeholder="e.g. PAPER1"
            className="h-8 w-36"
          />
        </label>
      </div>

      <div className="flex items-center gap-2">
        {health && (
          <div className="hidden items-center gap-1.5 sm:flex">
            <StatusBadge status={health.status} />
            <span className="text-xs text-text-muted">
              {health.trading_mode} · {health.market_data_mode}
            </span>
          </div>
        )}
        <button
          onClick={toggleTheme}
          className="rounded-md p-1.5 text-text-secondary hover:bg-hover hover:text-text-primary"
          aria-label="Toggle theme"
        >
          {theme === 'dark' ? <SunIcon className="h-4 w-4" /> : <MoonIcon className="h-4 w-4" />}
        </button>
      </div>
    </header>
  )
}
