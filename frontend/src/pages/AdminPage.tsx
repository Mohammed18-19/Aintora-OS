import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { adminApi } from '@/services/api'
import toast from 'react-hot-toast'
import { Search, ShieldCheck, Users, CalendarDays, Activity, PowerOff, Power, Loader2, Building2 } from 'lucide-react'
import clsx from 'clsx'
import { format } from 'date-fns'

export default function AdminPage() {
  const qc = useQueryClient()
  const [search, setSearch] = useState('')

  const { data: stats } = useQuery({
    queryKey: ['platform-stats'],
    queryFn: () => adminApi.platformStats().then(r => r.data),
  })

  const { data, isLoading } = useQuery({
    queryKey: ['admin-tenants', search],
    queryFn: () => adminApi.tenants({ search: search || undefined }).then(r => r.data),
  })

  const activateMut = useMutation({
    mutationFn: adminApi.activate,
    onSuccess: () => { toast.success('Tenant activated'); qc.invalidateQueries({ queryKey: ['admin-tenants'] }) },
  })
  const deactivateMut = useMutation({
    mutationFn: adminApi.deactivate,
    onSuccess: () => { toast.success('Tenant deactivated'); qc.invalidateQueries({ queryKey: ['admin-tenants'] }) },
  })

  const tenants = data?.tenants || []

  return (
    <div className="p-8 space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="p-3 rounded-2xl bg-accent/10 border border-accent/20">
          <ShieldCheck size={22} className="text-accent" />
        </div>
        <div>
          <h1 className="font-display text-2xl font-700 text-white">Super Admin</h1>
          <p className="text-white/40 text-sm">Platform-wide management</p>
        </div>
      </div>

      {/* Platform Stats */}
      {stats && (
        <div className="grid grid-cols-4 gap-4">
          {[
            { label: 'Total Businesses',  value: stats.total_tenants,    icon: Building2,    color: 'text-brand-400',   bg: 'bg-brand-400/10'   },
            { label: 'Active Businesses', value: stats.active_tenants,   icon: Activity,     color: 'text-emerald-400', bg: 'bg-emerald-400/10' },
            { label: 'Total Bookings',    value: stats.total_bookings,   icon: CalendarDays, color: 'text-amber-400',   bg: 'bg-amber-400/10'   },
            { label: 'Total Customers',   value: stats.total_customers,  icon: Users,        color: 'text-purple-400',  bg: 'bg-purple-400/10'  },
          ].map(({ label, value, icon: Icon, color, bg }) => (
            <div key={label} className="stat-card">
              <div className="flex items-center justify-between">
                <span className="text-white/40 text-xs font-semibold uppercase tracking-wider">{label}</span>
                <div className={clsx('p-2 rounded-xl', bg)}><Icon size={15} className={color} /></div>
              </div>
              <div className={clsx('font-display text-3xl font-700', color)}>{value}</div>
            </div>
          ))}
        </div>
      )}

      {/* Tenants Table */}
      <div className="card overflow-hidden">
        <div className="flex items-center justify-between p-5 border-b border-dark-border">
          <h2 className="font-semibold text-white flex items-center gap-2">
            <Building2 size={16} className="text-brand-400" /> All Businesses ({data?.total || 0})
          </h2>
          <div className="relative">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-white/30" />
            <input
              className="input pl-9 py-2 w-56 text-xs"
              placeholder="Search businesses…"
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
          </div>
        </div>

        <table className="w-full">
          <thead>
            <tr className="border-b border-dark-border">
              {['Business', 'Type', 'Plan', 'Bookings', 'Customers', 'Status', 'Joined', 'Actions'].map(h => (
                <th key={h} className="text-left text-white/40 text-xs font-semibold uppercase tracking-wider px-5 py-3.5">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {isLoading && (
              <tr><td colSpan={8} className="text-center py-10"><Loader2 className="animate-spin mx-auto text-brand-400" size={20} /></td></tr>
            )}
            {!isLoading && tenants.length === 0 && (
              <tr><td colSpan={8} className="text-center py-10 text-white/30 text-sm">No businesses found</td></tr>
            )}
            {tenants.map((t: any) => (
              <tr key={t.id} className="border-b border-dark-border/50 hover:bg-white/[0.02] transition-colors">
                <td className="px-5 py-4">
                  <div className="text-white font-medium text-sm">{t.name}</div>
                  <div className="text-white/30 text-xs font-mono">{t.slug}</div>
                </td>
                <td className="px-5 py-4">
                  <span className="badge bg-white/5 text-white/50 capitalize">{t.business_type || '–'}</span>
                </td>
                <td className="px-5 py-4">
                  <span className={clsx('badge', t.plan === 'free' ? 'bg-white/5 text-white/40' : 'bg-brand-400/10 text-brand-400')}>
                    {t.plan}
                  </span>
                </td>
                <td className="px-5 py-4 text-white/70 text-sm">{t.bookings_count}</td>
                <td className="px-5 py-4 text-white/70 text-sm">{t.customers_count}</td>
                <td className="px-5 py-4">
                  <span className={clsx(
                    'badge',
                    t.is_active ? 'bg-emerald-400/10 text-emerald-400' : 'bg-red-400/10 text-red-400'
                  )}>
                    <span className={clsx('w-1.5 h-1.5 rounded-full', t.is_active ? 'bg-emerald-400' : 'bg-red-400')} />
                    {t.is_active ? 'Active' : 'Inactive'}
                  </span>
                </td>
                <td className="px-5 py-4 text-white/40 text-xs">{format(new Date(t.created_at), 'dd/MM/yy')}</td>
                <td className="px-5 py-4">
                  {t.is_active ? (
                    <button
                      onClick={() => deactivateMut.mutate(t.id)}
                      className="btn-danger px-3 py-1.5 text-xs flex items-center gap-1"
                    >
                      <PowerOff size={11} /> Disable
                    </button>
                  ) : (
                    <button
                      onClick={() => activateMut.mutate(t.id)}
                      className="btn-success px-3 py-1.5 text-xs flex items-center gap-1"
                    >
                      <Power size={11} /> Enable
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
