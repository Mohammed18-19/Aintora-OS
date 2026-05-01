import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { bookingsApi } from '@/services/api'
import toast from 'react-hot-toast'
import { format } from 'date-fns'
import { ArrowLeft, Check, X, Calendar, User, Scissors, MessageCircle } from 'lucide-react'
import clsx from 'clsx'

const STATUS_COLOR: Record<string, string> = {
  pending:   'bg-amber-400/10 text-amber-400 border-amber-400/20',
  confirmed: 'bg-emerald-400/10 text-emerald-400 border-emerald-400/20',
  completed: 'bg-blue-400/10 text-blue-400 border-blue-400/20',
  cancelled: 'bg-red-400/10 text-red-400 border-red-400/20',
  rejected:  'bg-red-400/10 text-red-400 border-red-400/20',
}

function InfoRow({ icon: Icon, label, value }: any) {
  return (
    <div className="flex items-start gap-4 p-4 rounded-xl bg-white/[0.02]">
      <div className="p-2 rounded-lg bg-brand-600/10">
        <Icon size={15} className="text-brand-400" />
      </div>
      <div>
        <div className="text-white/40 text-xs uppercase tracking-wider font-semibold mb-1">{label}</div>
        <div className="text-white text-sm">{value || '–'}</div>
      </div>
    </div>
  )
}

export default function BookingDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const qc = useQueryClient()

  const { data: booking, isLoading } = useQuery({
    queryKey: ['booking', id],
    queryFn:  () => bookingsApi.get(id!).then(r => r.data),
  })

  const confirmMut = useMutation({
    mutationFn: () => bookingsApi.confirm(id!),
    onSuccess: () => { toast.success('Booking confirmed!'); qc.invalidateQueries({ queryKey: ['booking', id] }) },
  })
  const rejectMut = useMutation({
    mutationFn: () => bookingsApi.reject(id!),
    onSuccess: () => { toast.success('Booking rejected'); qc.invalidateQueries({ queryKey: ['booking', id] }) },
  })
  const cancelMut = useMutation({
    mutationFn: () => bookingsApi.cancel(id!),
    onSuccess: () => { toast.success('Booking cancelled'); qc.invalidateQueries({ queryKey: ['booking', id] }) },
  })

  if (isLoading) return <div className="p-8 text-white/40">Loading…</div>
  if (!booking)  return <div className="p-8 text-red-400">Booking not found.</div>

  return (
    <div className="p-8 max-w-2xl space-y-6 animate-fade-in">
      <button onClick={() => navigate('/bookings')} className="flex items-center gap-2 text-white/40 hover:text-white text-sm transition-colors">
        <ArrowLeft size={16} /> Back to bookings
      </button>

      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl font-700 text-white">{booking.booking_ref}</h1>
          <p className="text-white/40 text-sm mt-1">Created {format(new Date(booking.created_at), 'PPP')}</p>
        </div>
        <span className={clsx('badge border text-sm px-3 py-1.5', STATUS_COLOR[booking.status] || 'text-white/50')}>
          {booking.status}
        </span>
      </div>

      <div className="card p-6 space-y-3">
        <h2 className="font-semibold text-white mb-4">Booking Details</h2>
        <InfoRow icon={Calendar} label="Scheduled"  value={booking.scheduled_at ? format(new Date(booking.scheduled_at), 'PPPp') : '–'} />
        <InfoRow icon={Scissors} label="Service"    value={booking.service?.name} />
        <InfoRow icon={User}     label="Customer"   value={`${booking.customer?.name || 'Unknown'} · ${booking.customer?.number}`} />
        {booking.staff && <InfoRow icon={User} label="Staff" value={booking.staff.name} />}
        {booking.customer_notes && <InfoRow icon={MessageCircle} label="Customer Notes" value={booking.customer_notes} />}
        {booking.raw_message && (
          <div className="p-4 rounded-xl bg-dark-bg border border-dark-border">
            <div className="text-white/40 text-xs uppercase tracking-wider font-semibold mb-2">Original WhatsApp Message</div>
            <p className="text-white/70 text-sm italic">"{booking.raw_message}"</p>
          </div>
        )}
      </div>

      {/* Actions */}
      {booking.status === 'pending' && (
        <div className="card p-6">
          <h2 className="font-semibold text-white mb-4">Actions</h2>
          <div className="flex gap-3">
            <button onClick={() => confirmMut.mutate()} className="btn-success flex-1 flex items-center justify-center gap-2 py-3">
              <Check size={16} /> Confirm Booking
            </button>
            <button onClick={() => rejectMut.mutate()} className="btn-danger flex-1 flex items-center justify-center gap-2 py-3">
              <X size={16} /> Reject
            </button>
          </div>
        </div>
      )}

      {['confirmed', 'rescheduled'].includes(booking.status) && (
        <div className="card p-6">
          <button onClick={() => cancelMut.mutate()} className="btn-danger flex items-center gap-2">
            <X size={15} /> Cancel This Booking
          </button>
        </div>
      )}
    </div>
  )
}
