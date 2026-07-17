import { createContext, useContext, useEffect, useState } from 'react'
import { api } from '../api'

const AuthContext = createContext(null)

const STORAGE_KEY = 'gestioncours_auth'

export function AuthProvider({ children }) {
  const [token, setToken] = useState(null)
  const [student, setStudent] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) {
      try {
        const parsed = JSON.parse(raw)
        setToken(parsed.token)
        setStudent(parsed.student)
      } catch {
        localStorage.removeItem(STORAGE_KEY)
      }
    }
    setLoading(false)
  }, [])

  async function login(studentNumber, password) {
    const data = await api.login(studentNumber, password)
    setToken(data.access_token)
    setStudent(data.student)
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({ token: data.access_token, student: data.student }),
    )
    return data
  }

  function logout() {
    setToken(null)
    setStudent(null)
    localStorage.removeItem(STORAGE_KEY)
  }

  async function refreshStudent() {
    if (!token) return
    const profile = await api.getStudent(token)
    setStudent(profile)
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ token, student: profile }))
  }

  return (
    <AuthContext.Provider value={{ token, student, loading, login, logout, refreshStudent }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
