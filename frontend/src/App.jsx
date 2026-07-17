import { useState } from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import { ThemeProvider } from './context/ThemeContext'
import Navbar from './components/Navbar'
import Landing from './pages/Landing'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'

function Shell() {
  const { loading } = useAuth()
  const [notificationsOpen, setNotificationsOpen] = useState(false)

  if (loading) {
    return (
      <div className="flex min-h-dvh items-center justify-center text-brand-600">
        Chargement…
      </div>
    )
  }

  return (
    <>
      <Navbar onOpenNotifications={() => setNotificationsOpen(true)} />
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />
        <Route
          path="/dashboard"
          element={
            <Dashboard
              notificationsOpen={notificationsOpen}
              setNotificationsOpen={setNotificationsOpen}
            />
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  )
}

export default function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <BrowserRouter>
          <Shell />
        </BrowserRouter>
      </AuthProvider>
    </ThemeProvider>
  )
}
