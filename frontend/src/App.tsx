import { Center, Loader } from '@mantine/core'
import type { ReactNode } from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider, useAuth } from './auth'
import Layout from './components/Layout'
import AdminPage from './pages/AdminPage'
import Dashboard from './pages/Dashboard'
import Login from './pages/Login'
import ProjectPage from './pages/ProjectPage'
import Register from './pages/Register'

function Protected({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth()
  if (loading) {
    return (
      <Center mih="50vh">
        <Loader />
      </Center>
    )
  }
  return user ? <>{children}</> : <Navigate to="/login" replace />
}

function AdminOnly({ children }: { children: ReactNode }) {
  const { can } = useAuth()
  return can('Administrator') ? <>{children}</> : <Navigate to="/" replace />
}

function PublicOnly({ children }: { children: ReactNode }) {
  const { user } = useAuth()
  return user ? <Navigate to="/" replace /> : <>{children}</>
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Layout>
          <Routes>
            <Route path="/login" element={<PublicOnly><Login /></PublicOnly>} />
            <Route path="/register" element={<PublicOnly><Register /></PublicOnly>} />
            <Route path="/" element={<Protected><Dashboard /></Protected>} />
            <Route path="/projects/:id/:tab?" element={<Protected><ProjectPage /></Protected>} />
            <Route
              path="/admin"
              element={
                <Protected>
                  <AdminOnly>
                    <AdminPage />
                  </AdminOnly>
                </Protected>
              }
            />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Layout>
      </AuthProvider>
    </BrowserRouter>
  )
}
