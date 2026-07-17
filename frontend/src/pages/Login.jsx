import { useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Login() {
  const { login, student, loading } = useAuth()
  const navigate = useNavigate()
  const [studentNumber, setStudentNumber] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  if (!loading && student) return <Navigate to="/dashboard" replace />

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      await login(studentNumber.trim(), password)
      navigate('/dashboard')
    } catch (err) {
      setError(err.message || 'Connexion impossible')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <main className="mx-auto flex min-h-[calc(100dvh-64px)] max-w-md flex-col justify-center px-4 py-12">
      <div className="rounded-3xl bg-white/90 p-8 shadow-xl shadow-brand-900/10 backdrop-blur dark:bg-brand-800/70">
        <Link to="/" className="font-display text-2xl font-bold text-brand-600 dark:text-brand-200">
          GestionCours
        </Link>
        <h1 className="mt-4 text-xl font-semibold text-brand-800 dark:text-brand-50">Connexion étudiant</h1>
        <p className="mt-1 text-sm text-brand-600/80 dark:text-brand-200/70">
          Utilisez votre numéro d&apos;étudiant et votre mot de passe.
        </p>

        <form onSubmit={handleSubmit} className="mt-8 space-y-4">
          <label className="block">
            <span className="mb-1.5 block text-sm font-medium text-brand-700 dark:text-brand-200">
              Numéro d&apos;étudiant
            </span>
            <input
              type="text"
              autoComplete="username"
              required
              value={studentNumber}
              onChange={(e) => setStudentNumber(e.target.value)}
              className="w-full rounded-2xl border border-brand-200 bg-brand-50/50 px-4 py-3 text-brand-900 outline-none ring-brand-400 transition focus:ring-2 dark:border-brand-600 dark:bg-brand-900/50 dark:text-brand-50"
              placeholder="ex. 20250001"
            />
          </label>
          <label className="block">
            <span className="mb-1.5 block text-sm font-medium text-brand-700 dark:text-brand-200">
              Mot de passe
            </span>
            <input
              type="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-2xl border border-brand-200 bg-brand-50/50 px-4 py-3 text-brand-900 outline-none ring-brand-400 transition focus:ring-2 dark:border-brand-600 dark:bg-brand-900/50 dark:text-brand-50"
              placeholder="••••••••"
            />
          </label>

          {error && (
            <p className="rounded-xl bg-red-50 px-3 py-2 text-sm text-red-700 dark:bg-red-900/40 dark:text-red-200">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={submitting}
            className="w-full rounded-2xl bg-brand-600 py-3.5 font-semibold text-white shadow-lg shadow-brand-600/25 transition hover:bg-brand-700 disabled:opacity-60"
          >
            {submitting ? 'Connexion…' : 'Se connecter'}
          </button>
        </form>

        <p className="mt-6 text-center text-xs text-brand-600/70 dark:text-brand-300/60">
          Démo : 20250001 / password123
        </p>
      </div>
    </main>
  )
}
