import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import { authApi } from '@/services/api'
import toast from 'react-hot-toast'
import { Zap, Mail, Lock, ArrowRight, Loader2 } from 'lucide-react'

export default function LoginPage() {
  const navigate = useNavigate()
  const { setAuth } = useAuthStore()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    try {
      const res = await authApi.login(email, password)
// Set token in store FIRST so the /me call has Authorization header
setAuth(res.data.access_token, {
  id: res.data.user_id,
  email: email,
  full_name: '',
  role: res.data.role,
  tenant_id: res.data.tenant_id,
})
const meRes = await authApi.me()
setAuth(res.data.access_token, meRes.data)
      toast.success('Welcome back!')
      navigate('/dashboard')
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-dark-bg flex items-center justify-center p-4">
      {/* Background mesh */}
      <div className="fixed inset-0 bg-mesh-brand pointer-events-none" />

      <div className="relative w-full max-w-md animate-fade-in">
        {/* Logo */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-br from-brand-600 to-accent mb-5 shadow-lg shadow-brand-600/25">
            <Zap size={26} className="text-white" />
          </div>
          <h1 className="font-display text-3xl font-700 text-white mb-1">Welcome back</h1>
          <p className="text-white/40 text-sm">Sign in to your AINTORA dashboard</p>
        </div>

        {/* Card */}
        <div className="card p-8">
          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="space-y-1.5">
              <label className="text-white/60 text-xs font-semibold uppercase tracking-wider">Email</label>
              <div className="relative">
                <Mail size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-white/30" />
                <input
                  type="email"
                  className="input pl-10"
                  placeholder="you@business.com"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  required
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-white/60 text-xs font-semibold uppercase tracking-wider">Password</label>
              <div className="relative">
                <Lock size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-white/30" />
                <input
                  type="password"
                  className="input pl-10"
                  placeholder="••••••••"
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  required
                />
              </div>
            </div>

            <button type="submit" disabled={loading} className="btn-primary w-full flex items-center justify-center gap-2 py-3 text-base">
              {loading ? <Loader2 size={17} className="animate-spin" /> : (
                <>Sign in <ArrowRight size={16} /></>
              )}
            </button>
          </form>

          <p className="text-center text-sm text-white/40 mt-6">
            New business?{' '}
            <Link to="/register" className="text-brand-400 hover:text-brand-300 font-semibold transition-colors">
              Create account
            </Link>
          </p>
        </div>

        <p className="text-center text-xs text-white/20 mt-6">
          © 2024 AINTORA SYSTEMS
        </p>
      </div>
    </div>
  )
}
