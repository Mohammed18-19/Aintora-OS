import axios from 'axios'
import { useAuthStore } from '@/store/authStore'

const api = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      useAuthStore.getState().logout()
    }
    return Promise.reject(err)
  }
)

// ─── Auth ─────────────────────────────────────────────────────────────────────
export const authApi = {
  login: (email: string, password: string) =>
    api.post('/auth/login', { email, password }),
  register: (data: Record<string, string>) =>
    api.post('/auth/register', data),
  me: () => api.get('/auth/me'),
}

// ─── Bookings ─────────────────────────────────────────────────────────────────
export const bookingsApi = {
  list: (params?: Record<string, unknown>) => api.get('/bookings/', { params }),
  get:  (id: string) => api.get(`/bookings/${id}`),
  stats: () => api.get('/bookings/stats'),
  confirm: (id: string) => api.post(`/bookings/${id}/confirm`),
  reject:  (id: string, reason?: string) => api.post(`/bookings/${id}/reject`, { reason }),
  cancel:  (id: string) => api.post(`/bookings/${id}/cancel`),
  reschedule: (id: string, new_datetime: string) =>
    api.post(`/bookings/${id}/reschedule`, { new_datetime }),
}

// ─── Services ─────────────────────────────────────────────────────────────────
export const servicesApi = {
  list:   () => api.get('/services/'),
  create: (data: Record<string, unknown>) => api.post('/services/', data),
  update: (id: string, data: Record<string, unknown>) => api.put(`/services/${id}`, data),
  delete: (id: string) => api.delete(`/services/${id}`),
}

// ─── Staff ────────────────────────────────────────────────────────────────────
export const staffApi = {
  list:   () => api.get('/staff/'),
  create: (data: Record<string, unknown>) => api.post('/staff/', data),
}

// ─── Business Hours ───────────────────────────────────────────────────────────
export const hoursApi = {
  get:    () => api.get('/business-hours/'),
  update: (data: unknown[]) => api.put('/business-hours/', data),
}

// ─── WhatsApp Config ──────────────────────────────────────────────────────────
export const waApi = {
  get:  () => api.get('/whatsapp-config/'),
  save: (data: Record<string, string>) => api.post('/whatsapp-config/', data),
}

// ─── Admin ────────────────────────────────────────────────────────────────────
export const adminApi = {
  tenants:      (params?: Record<string, unknown>) => api.get('/admin/tenants', { params }),
  getTenant:    (id: string) => api.get(`/admin/tenants/${id}`),
  activate:     (id: string) => api.post(`/admin/tenants/${id}/activate`),
  deactivate:   (id: string) => api.post(`/admin/tenants/${id}/deactivate`),
  platformStats: () => api.get('/admin/stats/platform'),
}

export default api
