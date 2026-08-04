import { create } from 'zustand'
import { persist } from 'zustand/middleware'

type Theme = 'light' | 'dark' | 'system'

interface UIState {
  theme: Theme
  setTheme: (theme: Theme) => void
  sidebarCollapsed: boolean
  toggleSidebar: () => void
  selectedAccountId: string
  setSelectedAccountId: (accountId: string) => void
}

export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      theme: 'system',
      setTheme: (theme) => set({ theme }),
      sidebarCollapsed: false,
      toggleSidebar: () => set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
      selectedAccountId: '',
      setSelectedAccountId: (accountId) => set({ selectedAccountId: accountId }),
    }),
    { name: 'stock-signal-ui' },
  ),
)

export function applyThemeToDocument(theme: Theme) {
  const root = document.documentElement
  if (theme === 'system') {
    root.removeAttribute('data-theme')
  } else {
    root.setAttribute('data-theme', theme)
  }
}
