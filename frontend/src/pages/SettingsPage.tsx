import { useState, useEffect } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { waApi, hoursApi } from '@/services/api'
import toast from 'react-hot-toast'
import { MessageCircle, Clock, Copy, Check, Loader2, Save } from 'lucide-react'
import clsx from 'clsx'

const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

export default function SettingsPage() {
  const [tab, setTab] = useState<'whatsapp' | 'hours'>('whatsapp')

  return (
    <div className="p-8 space-y-6 animate-fade-in">
      <div>
        <h1 className="font-display text-2xl font-700 text-white">Settings</h1>
        <p className="text-white/40 text-sm mt-1">Configure your WhatsApp bot and business hours</p>
      </div>

      <div className="flex gap-2 border-b border-dark-border">
        {[
          { key: 'whatsapp', icon: MessageCircle, label: 'WhatsApp' },
          { key: 'hours',    icon: Clock,         label: 'Business Hours' },
        ].map(({ key, icon: Icon, label }) => (
          <button
            key={key}
            onClick={() => setTab(key as any)}
            className={clsx(
              'flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-all -mb-px',
              tab === key
                ? 'border-brand-600 text-brand-400'
                : 'border-transparent text-white/40 hover:text-white'
            )}
          >
            <Icon size={15} /> {label}
          </button>
        ))}
      </div>

      {tab === 'whatsapp' && <WhatsAppSettings />}
      {tab === 'hours'    && <BusinessHoursSettings />}
    </div>
  )
}

function WhatsAppSettings() {
  const { data: config } = useQuery({ queryKey: ['wa-config'], queryFn: () => waApi.get().then(r => r.data) })
  const [form, setForm] = useState({ phone_number_id: '', access_token: '', owner_whatsapp: '', waba_id: '' })
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    if (config?.configured) setForm(f => ({ ...f, phone_number_id: config.phone_number_id || '', owner_whatsapp: config.owner_whatsapp || '' }))
  }, [config])

  const saveMut = useMutation({
    mutationFn: () => waApi.save(form),
    onSuccess: (res) => {
      toast.success('WhatsApp config saved!')
      if (res.data.verify_token) toast.success(`Verify token: ${res.data.verify_token}`, { duration: 8000 })
    },
    onError: () => toast.error('Failed to save config'),
  })

  function copyWebhook() {
    navigator.clipboard.writeText(config?.webhook_url || '')
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const set = (k: string) => (e: React.ChangeEvent<HTMLInputElement>) => setForm(f => ({ ...f, [k]: e.target.value }))

  return (
    <div className="max-w-lg space-y-5">
      {config?.configured && (
        <div className="card p-4 border-emerald-400/20 bg-emerald-400/5">
          <div className="flex items-start gap-3">
            <Check size={16} className="text-emerald-400 mt-0.5" />
            <div>
              <div className="text-emerald-400 font-semibold text-sm mb-1">WhatsApp Connected</div>
              <div className="flex items-center gap-2">
                <code className="text-xs text-white/60 font-mono bg-dark-bg px-2 py-1 rounded-lg">{config.webhook_url}</code>
                <button onClick={copyWebhook} className="btn-ghost p-1.5">
                  {copied ? <Check size={13} className="text-emerald-400" /> : <Copy size={13} />}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {[
        { label: 'Phone Number ID', key: 'phone_number_id', placeholder: 'From Meta Developer Console' },
        { label: 'Access Token', key: 'access_token', placeholder: 'WhatsApp Cloud API token' },
        { label: 'WABA ID', key: 'waba_id', placeholder: 'WhatsApp Business Account ID' },
        { label: 'Owner WhatsApp', key: 'owner_whatsapp', placeholder: '212600000001 (no + sign)' },
      ].map(({ label, key, placeholder }) => (
        <div key={key} className="space-y-1.5">
          <label className="text-white/60 text-xs font-semibold uppercase tracking-wider">{label}</label>
          <input className="input" placeholder={placeholder} value={(form as any)[key]} onChange={set(key)} />
        </div>
      ))}

      <div className="card p-4 bg-amber-400/5 border-amber-400/20">
        <p className="text-amber-400/80 text-xs leading-relaxed">
          <strong>Setup steps:</strong> Go to Meta Developer Console → WhatsApp → API Setup → copy your Phone Number ID and generate a permanent token. Set the webhook URL above in your Meta app with the verify token shown after saving.
        </p>
      </div>

      <button
        onClick={() => saveMut.mutate()}
        disabled={saveMut.isPending || !form.phone_number_id || !form.access_token}
        className="btn-primary flex items-center gap-2 py-2.5"
      >
        {saveMut.isPending ? <Loader2 size={15} className="animate-spin" /> : <Save size={15} />}
        Save Configuration
      </button>
    </div>
  )
}

function BusinessHoursSettings() {
  const { data: hours } = useQuery({ queryKey: ['business-hours'], queryFn: () => hoursApi.get().then(r => r.data) })
  const [localHours, setLocalHours] = useState<any[]>([])

  useEffect(() => {
    if (hours?.length) setLocalHours(hours)
    else setLocalHours(DAYS.map((_, i) => ({ day_of_week: i, is_open: i < 6, opens_at: '09:00', closes_at: '19:00' })))
  }, [hours])

  const saveMut = useMutation({
    mutationFn: () => hoursApi.update(localHours),
    onSuccess: () => toast.success('Business hours saved!'),
  })

  function toggleDay(i: number) {
    setLocalHours(h => h.map((d, idx) => idx === i ? { ...d, is_open: !d.is_open } : d))
  }
  function setTime(i: number, key: string, val: string) {
    setLocalHours(h => h.map((d, idx) => idx === i ? { ...d, [key]: val } : d))
  }

  return (
    <div className="max-w-lg space-y-4">
      <div className="card overflow-hidden">
        {DAYS.map((day, i) => {
          const h = localHours[i] || { is_open: false }
          return (
            <div key={day} className={clsx('flex items-center gap-4 px-5 py-3.5', i < DAYS.length - 1 && 'border-b border-dark-border')}>
              <div className="w-28 text-sm font-medium text-white">{day}</div>
              <button
                onClick={() => toggleDay(i)}
                className={clsx(
                  'w-10 h-5 rounded-full transition-all relative',
                  h.is_open ? 'bg-brand-600' : 'bg-dark-border'
                )}
              >
                <span className={clsx(
                  'absolute top-0.5 w-4 h-4 rounded-full bg-white transition-all',
                  h.is_open ? 'right-0.5' : 'left-0.5'
                )} />
              </button>
              {h.is_open ? (
                <div className="flex items-center gap-2 flex-1">
                  <input type="time" className="input text-xs py-1.5 w-28" value={h.opens_at || '09:00'} onChange={e => setTime(i, 'opens_at', e.target.value)} />
                  <span className="text-white/30 text-xs">to</span>
                  <input type="time" className="input text-xs py-1.5 w-28" value={h.closes_at || '19:00'} onChange={e => setTime(i, 'closes_at', e.target.value)} />
                </div>
              ) : (
                <span className="text-white/30 text-sm flex-1">Closed</span>
              )}
            </div>
          )
        })}
      </div>

      <button onClick={() => saveMut.mutate()} disabled={saveMut.isPending} className="btn-primary flex items-center gap-2 py-2.5">
        {saveMut.isPending ? <Loader2 size={15} className="animate-spin" /> : <Save size={15} />}
        Save Hours
      </button>
    </div>
  )
}
