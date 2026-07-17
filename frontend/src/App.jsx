import { useState } from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import { ThemeProvider } from './context/ThemeContext'
import { SelectionProvider } from './context/SelectionContext'
import Navbar from './components/Navbar'
import Landing from './pages/Landing'
import Login from './pages/Login'
import Register from './pages/Register'
import SelectProgramme from './pages/SelectProgramme'
import Schedule from './pages/Schedule'

function Shell() {
  const { loading } = useAuth()
  const [notificationsOpen, setNotificationsOpen] = useState(false)

  if (loading) {
    return (
      <div className="flex min-h-dvh items-center justify-center font-display text-ist-600">
        IST Wayalghin…
      </div>
    )
  }

  return (
    <>
      <Navbar onOpenNotifications={() => setNotificationsOpen(true)} />
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/select" element={<SelectProgramme />} />
        <Route
          path="/schedule"
          element={
            <Schedule
              notificationsOpen={notificationsOpen}
              setNotificationsOpen={setNotificationsOpen}
            />
          }
        />
        <Route path="/dashboard" element={<Navigate to="/select" replace />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  )
}

export default function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <SelectionProvider>
          <BrowserRouter>
            <Shell />
          </BrowserRouter>
        </SelectionProvider>
      </AuthProvider>
    </ThemeProvider>
  )
}
