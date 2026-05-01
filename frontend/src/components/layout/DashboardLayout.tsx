import { Outlet, NavLink } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import {
  LayoutDashboard, CalendarDays, Scissors, Settings,
  LogOut, ShieldCheck, Zap
} from 'lucide-react'
import clsx from 'clsx'

const navItems = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/bookings',  icon: CalendarDays,    label: 'Bookings'  },
  { to: '/services',  icon: Scissors,        label: 'Services'  },
  { to: '/settings',  icon: Settings,        label: 'Settings'  },
]

export default function DashboardLayout() {
  const { user, logout } = useAuthStore()

  return (
    <div className="flex h-screen overflow-hidden">
      {/* ── Sidebar ─────────────────────────────────────────────────────── */}
      <aside className="w-64 shrink-0 bg-dark-card border-r border-dark-border flex flex-col">
        {/* Logo */}
        <div className="p-6 border-b border-dark-border">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-brand-600 to-accent flex items-center justify-center">
              <Zap size={18} className="text-white" />
            </div>
            <div>
              <div className="font-display font-700 text-white text-sm leading-none">AINTORA</div>
              <div className="text-[10px] text-accent font-semibold tracking-widest mt-0.5">SYSTEMS</div>
            </div>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 p-4 space-y-1">
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                clsx(
                  'flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all group',
                  isActive
                    ? 'bg-brand-600/15 text-brand-400 border border-brand-600/20'
                    : 'text-white/50 hover:text-white hover:bg-white/5'
                )
              }
            >
              <Icon size={17} />
              <span className="flex-1">{label}</span>
            </NavLink>
          ))}

          {user?.role === 'super_admin' && (
            <NavLink
              to="/admin"
              className={({ isActive }) =>
                clsx(
                  'flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all mt-4',
                  isActive
                    ? 'bg-accent/15 text-accent border border-accent/20'
                    : 'text-accent/60 hover:text-accent hover:bg-accent/5'
                )
              }
            >
              <ShieldCheck size={17} />
              <span>Super Admin</span>
            </NavLink>
          )}
        </nav>

        {/* User */}
        <div className="p-4 border-t border-dark-border">
          <div className="flex items-center gap-3 p-2 rounded-xl hover:bg-white/5 cursor-pointer group">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-brand-600 to-accent flex items-center justify-center text-white font-bold text-xs">
              {user?.full_name?.[0]?.toUpperCase() || user?.email?.[0]?.toUpperCase() || '?'}
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-white text-xs font-semibold truncate">{user?.full_name || user?.email}</div>
              <div className="text-white/40 text-[10px] capitalize">{user?.role}</div>
            </div>
            <button
              onClick={logout}
              className="text-white/30 hover:text-red-400 transition-colors p-1 rounded-lg"
              title="Logout"
            >
              <LogOut size={14} />
            </button>
          </div>
        </div>
      </aside>

      {/* ── Main ────────────────────────────────────────────────────────── */}
      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  )
}
