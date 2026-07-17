import { useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import Footer from '../components/Footer'

export default function Login() {
  const { login, student, loading } = useAuth()
  const navigate = useNavigate()
  const [studentNumber, setStudentNumber] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  if (!loading && student) return <Navigate to="/select" replace />

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      await login(studentNumber.trim(), password)
      navigate('/select')
    } catch (err) {
      setError(err.message || 'Connexion impossible')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="flex min-h-[calc(100dvh-64px)] flex-col">
      <main className="mx-auto flex w-full max-w-md flex-1 flex-col justify-center px-4 py-12">
        <div className="rounded-3xl border border-ist-100 bg-white p-8 shadow-xl shadow-ist-900/10 dark:border-ist-700 dark:bg-ist-800/80">
          <div className="mb-6 flex items-center gap-3">
            <img
              src="/ist-logo.jpeg"
              alt="IST"
              className="h-14 w-14 rounded-full object-cover ring-2 ring-gold-400"
            />
            <div>
              <p className="font-display text-2xl font-extrabold text-ist-600 dark:text-white">IST</p>
              <p className="text-sm text-ist-400">Wayalghin — Espace étudiant</p>
            </div>
          </div>

          <h1 className="text-xl font-semibold text-ist-700 dark:text-ist-50">Connexion</h1>
          <p className="mt-1 text-sm text-ist-500 dark:text-ist-300">
            Numéro d&apos;étudiant et mot de passe
          </p>

          <form onSubmit={handleSubmit} className="mt-8 space-y-4">
            <label className="block">
              <span className="mb-1.5 block text-sm font-semibold text-ist-600 dark:text-ist-200">
                Numéro d&apos;étudiant
              </span>
              <input
                type="text"
                autoComplete="username"
                required
                value={studentNumber}
                onChange={(e) => setStudentNumber(e.target.value)}
                className="w-full rounded-2xl border border-ist-200 bg-ist-50/60 px-4 py-3 text-ist-800 outline-none ring-gold-400 transition focus:ring-2 dark:border-ist-600 dark:bg-ist-900/50 dark:text-ist-50"
                placeholder="ex. 20250001"
              />
            </label>
            <label className="block">
              <span className="mb-1.5 block text-sm font-semibold text-ist-600 dark:text-ist-200">
                Mot de passe
              </span>
              <input
                type="password"
                autoComplete="current-password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full rounded-2xl border border-ist-200 bg-ist-50/60 px-4 py-3 text-ist-800 outline-none ring-gold-400 transition focus:ring-2 dark:border-ist-600 dark:bg-ist-900/50 dark:text-ist-50"
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
              className="w-full rounded-2xl bg-ist-600 py-3.5 font-bold text-white shadow-lg shadow-ist-600/25 transition hover:bg-ist-700 disabled:opacity-60"
            >
              {submitting ? 'Connexion…' : 'Continuer'}
            </button>
          </form>

          <p className="mt-6 text-center text-xs text-ist-400">
            Démo : 20250001 / password123 ·{' '}
            <Link to="/" className="underline">
              Accueil
            </Link>
          </p>
        </div>
      </main>
      <Footer />
    </div>
  )
}
