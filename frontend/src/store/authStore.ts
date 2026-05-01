import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface AuthUser {
  id: string
  email: string
  full_name: string
  role: string
  tenant_id: string | null
}

interface AuthStore {
  token: string | null
  user: AuthUser | null
  setAuth: (token: string, user: AuthUser) => void
  logout: () => void
  isAuthenticated: boolean
}

export const useAuthStore = create<AuthStore>()(
  persist(
    (set, _get) => ({
      token: null,
      user: null,
      isAuthenticated: false,
      setAuth: (token, user) => set({ token, user, isAuthenticated: true }),
      logout: () => {
        set({ token: null, user: null, isAuthenticated: false })
        window.location.href = '/login'
      },
    }),
    { name: 'aintora-auth' }
  )
)
