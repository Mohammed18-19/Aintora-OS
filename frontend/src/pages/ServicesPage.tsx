import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { servicesApi } from '@/services/api'
import toast from 'react-hot-toast'
import { Plus, Scissors, Edit3, Trash2, Clock, DollarSign, X, Loader2, Check } from 'lucide-react'
import clsx from 'clsx'

interface ServiceForm {
  name: string
  description: string
  duration_minutes: number
  price: number
  currency: string
  category: string
  nlp_aliases: string
}

const DEFAULT_FORM: ServiceForm = {
  name: '', description: '', duration_minutes: 60, price: 0,
  currency: 'MAD', category: '', nlp_aliases: '',
}

export default function ServicesPage() {
  const qc = useQueryClient()
  const [showModal, setShowModal] = useState(false)
  const [form, setForm] = useState<ServiceForm>(DEFAULT_FORM)
  const [editId, setEditId] = useState<string | null>(null)

  const { data, isLoading } = useQuery({
    queryKey: ['services'],
    queryFn:  () => servicesApi.list().then(r => r.data),
  })

  const createMut = useMutation({
    mutationFn: (data: any) => servicesApi.create(data),
    onSuccess: () => { toast.success('Service created!'); qc.invalidateQueries({ queryKey: ['services'] }); setShowModal(false); setForm(DEFAULT_FORM) },
    onError: () => toast.error('Failed to create service'),
  })
  const updateMut = useMutation({
    mutationFn: ({ id, data }: any) => servicesApi.update(id, data),
    onSuccess: () => { toast.success('Service updated!'); qc.invalidateQueries({ queryKey: ['services'] }); setShowModal(false); setEditId(null) },
  })
  const deleteMut = useMutation({
    mutationFn: servicesApi.delete,
    onSuccess: () => { toast.success('Service deactivated'); qc.invalidateQueries({ queryKey: ['services'] }) },
  })

  const services = data || []

  function openCreate() { setForm(DEFAULT_FORM); setEditId(null); setShowModal(true) }
  function openEdit(s: any) {
    setForm({ ...s, nlp_aliases: (s.nlp_aliases || []).join(', ') })
    setEditId(s.id); setShowModal(true)
  }

  function submit() {
    const payload = { ...form, nlp_aliases: form.nlp_aliases.split(',').map(s => s.trim()).filter(Boolean) }
    if (editId) updateMut.mutate({ id: editId, data: payload })
    else createMut.mutate(payload)
  }

  const set = (k: keyof ServiceForm) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
    setForm(f => ({ ...f, [k]: e.target.value }))

  return (
    <div className="p-8 space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl font-700 text-white">Services</h1>
          <p className="text-white/40 text-sm mt-1">Manage your bookable services</p>
        </div>
        <button onClick={openCreate} className="btn-primary flex items-center gap-2">
          <Plus size={16} /> Add Service
        </button>
      </div>

      {isLoading && <div className="flex justify-center py-12"><Loader2 className="animate-spin text-brand-400" size={24} /></div>}

      <div className="grid grid-cols-3 gap-4">
        {services.map((s: any) => (
          <div key={s.id} className={clsx('card p-5 space-y-3 transition-all', !s.is_active && 'opacity-50')}>
            <div className="flex items-start justify-between">
              <div className="p-2.5 rounded-xl bg-brand-600/10 border border-brand-600/20">
                <Scissors size={16} className="text-brand-400" />
              </div>
              <div className="flex gap-1">
                <button onClick={() => openEdit(s)} className="btn-ghost p-2"><Edit3 size={13} /></button>
                <button onClick={() => deleteMut.mutate(s.id)} className="btn-ghost p-2 hover:text-red-400"><Trash2 size={13} /></button>
              </div>
            </div>
            <div>
              <h3 className="font-semibold text-white">{s.name}</h3>
              {s.description && <p className="text-white/40 text-xs mt-1 line-clamp-2">{s.description}</p>}
            </div>
            <div className="flex items-center gap-3 text-xs text-white/40">
              <span className="flex items-center gap-1"><Clock size={11} /> {s.duration_minutes} min</span>
              <span className="flex items-center gap-1"><DollarSign size={11} /> {s.price} {s.currency}</span>
            </div>
            {s.nlp_aliases?.length > 0 && (
              <div className="flex flex-wrap gap-1">
                {s.nlp_aliases.slice(0, 3).map((a: string) => (
                  <span key={a} className="badge bg-white/5 text-white/40 text-[10px]">{a}</span>
                ))}
                {s.nlp_aliases.length > 3 && <span className="badge bg-white/5 text-white/30 text-[10px]">+{s.nlp_aliases.length - 3}</span>}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="card p-6 w-full max-w-md animate-slide-up">
            <div className="flex items-center justify-between mb-6">
              <h2 className="font-display text-xl font-700 text-white">{editId ? 'Edit Service' : 'New Service'}</h2>
              <button onClick={() => setShowModal(false)} className="btn-ghost p-2"><X size={16} /></button>
            </div>

            <div className="space-y-4">
              {[
                { label: 'Service Name', key: 'name', placeholder: 'e.g. Coupe Femme' },
                { label: 'Description', key: 'description', placeholder: 'Short description…' },
                { label: 'Category', key: 'category', placeholder: 'e.g. hair, nails, treatment' },
                { label: 'NLP Aliases (comma-separated)', key: 'nlp_aliases', placeholder: 'coupe, haircut, قص' },
              ].map(({ label, key, placeholder }) => (
                <div key={key} className="space-y-1.5">
                  <label className="text-white/60 text-xs font-semibold uppercase tracking-wider">{label}</label>
                  <input className="input" placeholder={placeholder} value={(form as any)[key]} onChange={set(key as keyof ServiceForm)} />
                </div>
              ))}

              <div className="grid grid-cols-3 gap-3">
                {[
                  { label: 'Duration (min)', key: 'duration_minutes', type: 'number' },
                  { label: 'Price', key: 'price', type: 'number' },
                  { label: 'Currency', key: 'currency', type: 'text' },
                ].map(({ label, key, type }) => (
                  <div key={key} className="space-y-1.5">
                    <label className="text-white/60 text-xs font-semibold uppercase tracking-wider">{label}</label>
                    <input className="input" type={type} value={(form as any)[key]} onChange={set(key as keyof ServiceForm)} />
                  </div>
                ))}
              </div>
            </div>

            <div className="flex gap-3 mt-6">
              <button onClick={() => setShowModal(false)} className="btn-ghost flex-1">Cancel</button>
              <button
                onClick={submit}
                disabled={createMut.isPending || updateMut.isPending}
                className="btn-primary flex-1 flex items-center justify-center gap-2"
              >
                {(createMut.isPending || updateMut.isPending)
                  ? <Loader2 size={15} className="animate-spin" />
                  : <><Check size={15} /> {editId ? 'Update' : 'Create'}</>
                }
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
