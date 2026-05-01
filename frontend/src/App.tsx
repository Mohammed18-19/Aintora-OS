import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import LoginPage from '@/pages/LoginPage'
import RegisterPage from '@/pages/RegisterPage'
import DashboardLayout from '@/components/layout/DashboardLayout'
import DashboardHome from '@/pages/DashboardHome'
import BookingsPage from '@/pages/BookingsPage'
import BookingDetailPage from '@/pages/BookingDetailPage'
import ServicesPage from '@/pages/ServicesPage'
import SettingsPage from '@/pages/SettingsPage'
import AdminPage from '@/pages/AdminPage'

function RequireAuth({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthStore()
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />
}

function RequireAdmin({ children }: { children: React.ReactNode }) {
  const { user } = useAuthStore()
  if (user?.role !== 'super_admin') return <Navigate to="/dashboard" replace />
  return <>{children}</>
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      <Route path="/" element={<RequireAuth><DashboardLayout /></RequireAuth>}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<DashboardHome />} />
        <Route path="bookings" element={<BookingsPage />} />
        <Route path="bookings/:id" element={<BookingDetailPage />} />
        <Route path="services" element={<ServicesPage />} />
        <Route path="settings" element={<SettingsPage />} />
        <Route
          path="admin"
          element={
            <RequireAdmin>
              <AdminPage />
            </RequireAdmin>
          }
        />
      </Route>

      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}
