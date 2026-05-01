import { useState } from 'react'
import { useQuery, useQueryClient, useMutation } from '@tanstack/react-query'
import { bookingsApi } from '@/services/api'
import { Link } from 'react-router-dom'
import toast from 'react-hot-toast'
import { format } from 'date-fns'
import { Search, Check, X, ChevronRight, Loader2 } from 'lucide-react'
import clsx from 'clsx'

const STATUS_FILTERS = ['all', 'pending', 'confirmed', 'completed', 'cancelled', 'rejected']

const STATUS_COLOR: Record<string, string> = {
  pending:     'bg-amber-400/10 text-amber-400 border-amber-400/20',
  confirmed:   'bg-emerald-400/10 text-emerald-400 border-emerald-400/20',
  completed:   'bg-blue-400/10 text-blue-400 border-blue-400/20',
  cancelled:   'bg-red-400/10 text-red-400 border-red-400/20',
  rejected:    'bg-red-400/10 text-red-400 border-red-400/20',
  rescheduled: 'bg-purple-400/10 text-purple-400 border-purple-400/20',
}

export default function BookingsPage() {
  const qc = useQueryClient()
  const [statusFilter, setStatusFilter] = useState('all')
  const [search, setSearch] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['bookings', statusFilter],
    queryFn:  () => bookingsApi.list({
      status: statusFilter === 'all' ? undefined : statusFilter,
      limit: 50,
    }).then(r => r.data),
  })

  const confirmMut = useMutation({
    mutationFn: bookingsApi.confirm,
    onSuccess: () => { toast.success('Booking confirmed ✅'); qc.invalidateQueries({ queryKey: ['bookings'] }) },
  })
  const rejectMut = useMutation({
    mutationFn: (id: string) => bookingsApi.reject(id),
    onSuccess: () => { toast.success('Booking rejected'); qc.invalidateQueries({ queryKey: ['bookings'] }) },
  })

  const bookings = (data?.bookings || []).filter((b: any) =>
    !search || b.customer_name?.toLowerCase().includes(search.toLowerCase()) ||
    b.customer_number?.includes(search) || b.service?.toLowerCase().includes(search.toLowerCase()) ||
    b.booking_ref?.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="p-8 space-y-6 animate-fade-in">
      <div>
        <h1 className="font-display text-2xl font-700 text-white">Bookings</h1>
        <p className="text-white/40 text-sm mt-1">Manage all your appointments</p>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-xs">
          <Search size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-white/30" />
          <input
            className="input pl-10"
            placeholder="Search bookings…"
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
        </div>

        <div className="flex items-center gap-1 bg-dark-card border border-dark-border rounded-xl p-1">
          {STATUS_FILTERS.map(s => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              className={clsx(
                'px-3 py-1.5 rounded-lg text-xs font-semibold capitalize transition-all',
                statusFilter === s
                  ? 'bg-brand-600 text-white'
                  : 'text-white/40 hover:text-white hover:bg-white/5'
              )}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      {/* Table */}
      <div className="card overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-dark-border">
              {['Ref', 'Customer', 'Service', 'Date & Time', 'Status', 'Actions'].map(h => (
                <th key={h} className="text-left text-white/40 text-xs font-semibold uppercase tracking-wider px-5 py-4">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {isLoading && (
              <tr><td colSpan={6} className="text-center py-12 text-white/30"><Loader2 className="animate-spin mx-auto" size={20} /></td></tr>
            )}
            {!isLoading && bookings.length === 0 && (
              <tr><td colSpan={6} className="text-center py-12 text-white/30 text-sm">No bookings found</td></tr>
            )}
            {bookings.map((b: any) => (
              <tr key={b.id} className="border-b border-dark-border/50 hover:bg-white/[0.02] transition-colors">
                <td className="px-5 py-4">
                  <span className="font-mono text-xs text-brand-400">{b.booking_ref}</span>
                </td>
                <td className="px-5 py-4">
                  <div className="text-white text-sm font-medium">{b.customer_name || '–'}</div>
                  <div className="text-white/40 text-xs">{b.customer_number}</div>
                </td>
                <td className="px-5 py-4 text-white/70 text-sm">{b.service || '–'}</td>
                <td className="px-5 py-4">
                  {b.scheduled_at ? (
                    <div>
                      <div className="text-white text-sm">{format(new Date(b.scheduled_at), 'dd/MM/yyyy')}</div>
                      <div className="text-white/40 text-xs">{format(new Date(b.scheduled_at), 'HH:mm')}</div>
                    </div>
                  ) : '–'}
                </td>
                <td className="px-5 py-4">
                  <span className={clsx('badge border', STATUS_COLOR[b.status] || 'text-white/50')}>
                    {b.status}
                  </span>
                </td>
                <td className="px-5 py-4">
                  <div className="flex items-center gap-2">
                    {b.status === 'pending' && (
                      <>
                        <button
                          onClick={() => confirmMut.mutate(b.id)}
                          className="btn-success px-3 py-1.5 text-xs"
                        >
                          <Check size={13} className="inline mr-1" />Confirm
                        </button>
                        <button
                          onClick={() => rejectMut.mutate(b.id)}
                          className="btn-danger px-3 py-1.5 text-xs"
                        >
                          <X size={13} className="inline mr-1" />Reject
                        </button>
                      </>
                    )}
                    <Link to={`/bookings/${b.id}`} className="btn-ghost px-2 py-1.5 text-xs">
                      <ChevronRight size={14} />
                    </Link>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
