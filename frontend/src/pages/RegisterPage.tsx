import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import { authApi } from '@/services/api'
import toast from 'react-hot-toast'
import { Zap, Loader2, ArrowRight, Building2, User, Mail, Lock, Phone } from 'lucide-react'

const BUSINESS_TYPES = [
  { value: 'salon',       label: '💇 Salon' },
  { value: 'clinic',      label: '🏥 Clinic' },
  { value: 'spa',         label: '💆 Spa' },
  { value: 'barbershop',  label: '✂️ Barbershop' },
  { value: 'dental',      label: '🦷 Dental' },
  { value: 'fitness',     label: '🏋️ Fitness' },
  { value: 'other',       label: '📋 Other' },
]

export default function RegisterPage() {
  const navigate = useNavigate()
  const { setAuth } = useAuthStore()
  const [loading, setLoading] = useState(false)
  const [form, setForm] = useState({
    email: '', password: '', full_name: '',
    business_name: '', business_type: 'salon', phone: '',
  })

  const set = (k: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setForm(f => ({ ...f, [k]: e.target.value }))

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    try {
      const res = await authApi.register(form)
      const meRes = await authApi.me()
      setAuth(res.data.access_token, meRes.data)
      toast.success('Account created! Welcome to AINTORA 🎉')
      navigate('/dashboard')
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  const Field = ({ icon: Icon, label, ...props }: any) => (
    <div className="space-y-1.5">
      <label className="text-white/60 text-xs font-semibold uppercase tracking-wider">{label}</label>
      <div className="relative">
        <Icon size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-white/30" />
        <input className="input pl-10" {...props} />
      </div>
    </div>
  )

  return (
    <div className="min-h-screen bg-dark-bg flex items-center justify-center p-4">
      <div className="fixed inset-0 bg-mesh-brand pointer-events-none" />

      <div className="relative w-full max-w-lg animate-fade-in">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-br from-brand-600 to-accent mb-5 shadow-lg shadow-brand-600/25">
            <Zap size={26} className="text-white" />
          </div>
          <h1 className="font-display text-3xl font-700 text-white mb-1">Create your account</h1>
          <p className="text-white/40 text-sm">Get your WhatsApp booking bot live in minutes</p>
        </div>

        <div className="card p-8">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <Field icon={User}  label="Full Name"     type="text"  placeholder="Your name"       value={form.full_name}     onChange={set('full_name')}     required />
              <Field icon={Phone} label="Phone"         type="tel"   placeholder="+212600000000"    value={form.phone}         onChange={set('phone')} />
            </div>
            <Field icon={Building2} label="Business Name" type="text" placeholder="Salon Nour" value={form.business_name} onChange={set('business_name')} required />

            <div className="space-y-1.5">
              <label className="text-white/60 text-xs font-semibold uppercase tracking-wider">Business Type</label>
              <select className="input" value={form.business_type} onChange={set('business_type')}>
                {BUSINESS_TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
              </select>
            </div>

            <div className="border-t border-dark-border pt-4 space-y-4">
              <Field icon={Mail} label="Email" type="email" placeholder="you@business.com" value={form.email} onChange={set('email')} required />
              <Field icon={Lock} label="Password" type="password" placeholder="Min. 8 characters" value={form.password} onChange={set('password')} required minLength={8} />
            </div>

            <button type="submit" disabled={loading} className="btn-primary w-full flex items-center justify-center gap-2 py-3 text-base mt-2">
              {loading ? <Loader2 size={17} className="animate-spin" /> : <>Create Account <ArrowRight size={16} /></>}
            </button>
          </form>

          <p className="text-center text-sm text-white/40 mt-5">
            Already have an account?{' '}
            <Link to="/login" className="text-brand-400 hover:text-brand-300 font-semibold transition-colors">Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  )
}
