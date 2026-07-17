import { useEffect, useMemo, useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useSelection } from '../context/SelectionContext'
import { api } from '../api'
import Footer from '../components/Footer'

const LEVELS = ['L1', 'L2', 'L3', 'Master', 'Doctorat']

export default function Register() {
  const { register, student, loading } = useAuth()
  const { setSelection } = useSelection()
  const navigate = useNavigate()

  const [form, setForm] = useState({
    student_number: '',
    first_name: '',
    last_name: '',
    email: '',
    password: '',
    level: 'L1',
    filiere_id: '',
  })
  const [filieres, setFilieres] = useState([])
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        const list = await api.getPublicFilieres(form.level)
        if (cancelled) return
        setFilieres(list)
        setForm((f) => ({
          ...f,
          filiere_id: list.some((x) => String(x.id) === String(f.filiere_id))
            ? f.filiere_id
            : list[0]
              ? String(list[0].id)
              : '',
        }))
      } catch (err) {
        if (!cancelled) setError(err.message)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [form.level])

  const selectedFiliere = useMemo(
    () => filieres.find((f) => String(f.id) === String(form.filiere_id)),
    [filieres, form.filiere_id],
  )

  if (!loading && student) return <Navigate to="/select" replace />

  function update(field, value) {
    setForm((f) => ({ ...f, [field]: value }))
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    if (!form.filiere_id) {
      setError('Choisissez une filière')
      return
    }
    setSubmitting(true)
    try {
      const data = await register({
        student_number: form.student_number.trim().toUpperCase(),
        first_name: form.first_name.trim(),
        last_name: form.last_name.trim(),
        email: form.email.trim(),
        password: form.password,
        filiere_id: Number(form.filiere_id),
        level: form.level,
      })
      if (selectedFiliere) {
        setSelection({
          level: selectedFiliere.level || form.level,
          filiereId: selectedFiliere.id,
          filiereName: selectedFiliere.name,
        })
      }
      navigate('/schedule')
      return data
    } catch (err) {
      setError(err.message || 'Inscription impossible')
    } finally {
      setSubmitting(false)
    }
  }

  const fieldClass =
    'w-full rounded-2xl border border-ist-200 bg-ist-50/60 px-4 py-3 text-ist-800 outline-none ring-gold-400 transition focus:ring-2 dark:border-ist-600 dark:bg-ist-900/50 dark:text-ist-50'

  return (
    <div className="flex min-h-[calc(100dvh-64px)] flex-col">
      <main className="mx-auto flex w-full max-w-lg flex-1 flex-col justify-center px-4 py-10">
        <div className="rounded-3xl border border-ist-100 bg-white p-8 shadow-xl shadow-ist-900/10 dark:border-ist-700 dark:bg-ist-800/80">
          <div className="mb-6 flex items-center gap-3">
            <img
              src="/ist-logo.jpeg"
              alt="IST"
              className="h-14 w-14 rounded-full object-cover ring-2 ring-gold-400"
            />
            <div>
              <p className="font-display text-2xl font-extrabold text-ist-600 dark:text-white">IST</p>
              <p className="text-sm text-ist-400">Créer un compte étudiant</p>
            </div>
          </div>

          <h1 className="text-xl font-semibold text-ist-700 dark:text-ist-50">Inscription</h1>
          <p className="mt-1 text-sm text-ist-500 dark:text-ist-300">
            Créez votre compte pour consulter et télécharger votre emploi du temps.
          </p>

          <form onSubmit={handleSubmit} className="mt-6 space-y-3">
            <div className="grid gap-3 sm:grid-cols-2">
              <label className="block text-sm">
                <span className="mb-1 block font-semibold text-ist-600 dark:text-ist-200">Prénom</span>
                <input
                  required
                  className={fieldClass}
                  value={form.first_name}
                  onChange={(e) => update('first_name', e.target.value)}
                />
              </label>
              <label className="block text-sm">
                <span className="mb-1 block font-semibold text-ist-600 dark:text-ist-200">Nom</span>
                <input
                  required
                  className={fieldClass}
                  value={form.last_name}
                  onChange={(e) => update('last_name', e.target.value)}
                />
              </label>
            </div>

            <label className="block text-sm">
              <span className="mb-1 block font-semibold text-ist-600 dark:text-ist-200">
                Numéro d&apos;étudiant (INE)
              </span>
              <input
                required
                pattern="IST\.W[0-9]+"
                title="Doit commencer par IST.W suivi de chiffres"
                className={fieldClass}
                value={form.student_number}
                onChange={(e) => update('student_number', e.target.value.toUpperCase())}
                placeholder="IST.W20250001"
              />
              <span className="mt-1 block text-xs text-ist-400">
                Format obligatoire : IST.W + chiffres (ex. IST.W20250001)
              </span>
            </label>

            <label className="block text-sm">
              <span className="mb-1 block font-semibold text-ist-600 dark:text-ist-200">E-mail</span>
              <input
                type="email"
                required
                className={fieldClass}
                value={form.email}
                onChange={(e) => update('email', e.target.value)}
                placeholder="prenom.nom@exemple.com"
              />
            </label>

            <label className="block text-sm">
              <span className="mb-1 block font-semibold text-ist-600 dark:text-ist-200">
                Mot de passe (6 caractères min.)
              </span>
              <input
                type="password"
                required
                minLength={6}
                className={fieldClass}
                value={form.password}
                onChange={(e) => update('password', e.target.value)}
              />
            </label>

            <label className="block text-sm">
              <span className="mb-1 block font-semibold text-ist-600 dark:text-ist-200">Année</span>
              <select
                className={fieldClass}
                value={form.level}
                onChange={(e) => update('level', e.target.value)}
              >
                {LEVELS.map((l) => (
                  <option key={l} value={l}>
                    {l}
                  </option>
                ))}
              </select>
            </label>

            <label className="block text-sm">
              <span className="mb-1 block font-semibold text-ist-600 dark:text-ist-200">Filière</span>
              <select
                required
                className={fieldClass}
                value={form.filiere_id}
                onChange={(e) => update('filiere_id', e.target.value)}
              >
                {filieres.length === 0 && <option value="">Aucune filière</option>}
                {filieres.map((f) => (
                  <option key={f.id} value={f.id}>
                    {f.name}
                  </option>
                ))}
              </select>
            </label>

            {error && (
              <p className="rounded-xl bg-red-50 px-3 py-2 text-sm text-red-700 dark:bg-red-900/40 dark:text-red-200">
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={submitting}
              className="w-full rounded-2xl bg-gold-400 py-3.5 font-bold text-ist-700 shadow-md transition hover:bg-gold-300 disabled:opacity-60"
            >
              {submitting ? 'Création…' : 'Créer mon compte'}
            </button>
          </form>

          <p className="mt-5 text-center text-sm text-ist-500">
            Déjà inscrit ?{' '}
            <Link to="/login" className="font-semibold text-ist-600 underline dark:text-gold-400">
              Se connecter
            </Link>
          </p>
        </div>
      </main>
      <Footer />
    </div>
  )
}
