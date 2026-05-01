import { useQuery } from '@tanstack/react-query'
import { bookingsApi } from '@/services/api'
import { useAuthStore } from '@/store/authStore'
import { CalendarDays, CheckCircle, Clock, XCircle, TrendingUp, MessageCircle, Zap } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'
import { format } from 'date-fns'
import clsx from 'clsx'

const STATUS_CONFIG: Record<string, { color: string; bg: string; label: string }> = {
  pending:     { color: 'text-amber-400',   bg: 'bg-amber-400/10',   label: 'Pending'    },
  confirmed:   { color: 'text-emerald-400', bg: 'bg-emerald-400/10', label: 'Confirmed'  },
  rejected:    { color: 'text-red-400',     bg: 'bg-red-400/10',     label: 'Rejected'   },
  cancelled:   { color: 'text-red-400',     bg: 'bg-red-400/10',     label: 'Cancelled'  },
  completed:   { color: 'text-blue-400',    bg: 'bg-blue-400/10',    label: 'Completed'  },
  rescheduled: { color: 'text-purple-400',  bg: 'bg-purple-400/10',  label: 'Rescheduled'},
}

function StatusBadge({ status }: { status: string }) {
  const cfg = STATUS_CONFIG[status] || { color: 'text-white/50', bg: 'bg-white/5', label: status }
  return (
    <span className={clsx('badge', cfg.bg, cfg.color)}>
      <span className={clsx('w-1.5 h-1.5 rounded-full', cfg.bg, cfg.color, 'bg-current')} />
      {cfg.label}
    </span>
  )
}

export default function DashboardHome() {
  const { user } = useAuthStore()

  const { data: statsData } = useQuery({
    queryKey: ['booking-stats'],
    queryFn:  () => bookingsApi.stats().then(r => r.data),
  })

  const { data: bookingsData } = useQuery({
    queryKey: ['bookings-recent'],
    queryFn:  () => bookingsApi.list({ limit: 8 }).then(r => r.data),
  })

  const stats = statsData || {}
  const recentBookings = bookingsData?.bookings || []

  const chartData = [
    { name: 'Pending',    value: stats.pending    || 0, fill: '#f59e0b' },
    { name: 'Confirmed',  value: stats.confirmed  || 0, fill: '#10b981' },
    { name: 'Completed',  value: stats.completed  || 0, fill: '#3b82f6' },
    { name: 'Cancelled',  value: stats.cancelled  || 0, fill: '#ef4444' },
  ]

  return (
    <div className="p-8 space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="font-display text-2xl font-700 text-white">
            Good {new Date().getHours() < 12 ? 'morning' : new Date().getHours() < 18 ? 'afternoon' : 'evening'},{' '}
            <span className="text-brand-400">{user?.full_name?.split(' ')[0] || 'there'}</span> 👋
          </h1>
          <p className="text-white/40 text-sm mt-1">{format(new Date(), 'EEEE, MMMM d, yyyy')}</p>
        </div>
        <div className="flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-400/10 border border-emerald-400/20">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span className="text-emerald-400 text-xs font-semibold">Bot Active</span>
        </div>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-4 gap-4">
        {[
          { label: 'Total Bookings', value: stats.total || 0,     icon: CalendarDays, color: 'text-brand-400',   bg: 'bg-brand-400/10'   },
          { label: 'Pending',        value: stats.pending || 0,   icon: Clock,        color: 'text-amber-400',   bg: 'bg-amber-400/10'   },
          { label: 'Confirmed',      value: stats.confirmed || 0, icon: CheckCircle,  color: 'text-emerald-400', bg: 'bg-emerald-400/10' },
          { label: 'Cancelled',      value: stats.cancelled || 0, icon: XCircle,      color: 'text-red-400',     bg: 'bg-red-400/10'     },
        ].map(({ label, value, icon: Icon, color, bg }) => (
          <div key={label} className="stat-card">
            <div className="flex items-center justify-between">
              <span className="text-white/40 text-xs font-semibold uppercase tracking-wider">{label}</span>
              <div className={clsx('p-2 rounded-xl', bg)}>
                <Icon size={15} className={color} />
              </div>
            </div>
            <div className={clsx('font-display text-3xl font-700', color)}>{value}</div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-5 gap-6">
        {/* Chart */}
        <div className="col-span-2 card p-6">
          <h2 className="font-semibold text-white mb-5 flex items-center gap-2">
            <TrendingUp size={16} className="text-brand-400" /> Booking Status
          </h2>
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={chartData} barSize={28}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e1e32" />
              <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#6b7280' }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 11, fill: '#6b7280' }} axisLine={false} tickLine={false} />
              <Tooltip
                contentStyle={{ background: '#12121f', border: '1px solid #1e1e32', borderRadius: 12, fontSize: 12 }}
                labelStyle={{ color: '#fff' }}
              />
              <Bar dataKey="value" radius={[6, 6, 0, 0]} fill="#3355ff" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Recent Bookings */}
        <div className="col-span-3 card p-6">
          <h2 className="font-semibold text-white mb-5 flex items-center gap-2">
            <MessageCircle size={16} className="text-brand-400" /> Recent Bookings
          </h2>
          <div className="space-y-2">
            {recentBookings.length === 0 && (
              <div className="text-center py-8 text-white/30 text-sm">No bookings yet. Share your WhatsApp link!</div>
            )}
            {recentBookings.map((b: any) => (
              <div key={b.id} className="flex items-center gap-3 p-3 rounded-xl hover:bg-white/5 transition-colors cursor-pointer">
                <div className="w-9 h-9 rounded-xl bg-brand-600/15 border border-brand-600/20 flex items-center justify-center">
                  <span className="text-brand-400 font-bold text-xs">{b.customer_name?.[0]?.toUpperCase() || '#'}</span>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-white text-sm font-medium truncate">{b.customer_name || b.customer_number}</div>
                  <div className="text-white/40 text-xs">{b.service} · {b.scheduled_at ? format(new Date(b.scheduled_at), 'dd/MM HH:mm') : '–'}</div>
                </div>
                <StatusBadge status={b.status} />
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* WhatsApp Bot Info */}
      <div className="card p-6 bg-gradient-to-r from-brand-600/10 to-accent/10 border-brand-600/20">
        <div className="flex items-start gap-4">
          <div className="p-3 rounded-2xl bg-brand-600/20 border border-brand-600/30">
            <Zap size={22} className="text-brand-400" />
          </div>
          <div>
            <h3 className="font-semibold text-white mb-1">WhatsApp Bot is running</h3>
            <p className="text-white/50 text-sm">
              Your webhook URL:{' '}
              <code className="text-brand-300 font-mono bg-dark-bg px-2 py-0.5 rounded-lg text-xs">
                /api/v1/webhook/{user?.tenant_id ? 'your-slug' : 'slug'}
              </code>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
