import { useState } from 'react'
import { Outlet } from 'react-router-dom'
import { Toaster } from 'sonner'
import { Sidebar } from './Sidebar'
import { TopBar } from './TopBar'
import { BottomTabBar, MobileNavDrawer } from './MobileNav'

export function AppShell() {
  const [mobileNavOpen, setMobileNavOpen] = useState(false)

  return (
    <div className="flex h-screen overflow-hidden bg-page">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <TopBar onOpenMobileNav={() => setMobileNavOpen(true)} />
        <main className="scroll-thin flex-1 overflow-y-auto p-3 md:p-6">
          <Outlet />
        </main>
        <BottomTabBar onMore={() => setMobileNavOpen(true)} />
      </div>
      <MobileNavDrawer open={mobileNavOpen} onClose={() => setMobileNavOpen(false)} />
      <Toaster richColors position="top-right" />
    </div>
  )
}
