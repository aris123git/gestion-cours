import { useEffect, useMemo, useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useSelection } from '../context/SelectionContext'
import { api } from '../api'
import Footer from '../components/Footer'

const LEVELS = ['L1', 'L2', 'L3', 'Master', 'Doctorat']

export default function SelectProgramme() {
  const { token, student, loading } = useAuth()
  const { selection, setSelection } = useSelection()
  const navigate = useNavigate()
  const [level, setLevel] = useState(student?.level || 'L1')
  const [filiereId, setFiliereId] = useState('')
  const [filieres, setFilieres] = useState([])
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    if (student?.level) setLevel(student.level)
  }, [student])

  useEffect(() => {
    if (!token) return
    let cancelled = false
    ;(async () => {
      setBusy(true)
      setError('')
      try {
        const list = await api.getFilieres(token, level || undefined)
        if (cancelled) return
        setFilieres(list)
        const preferred =
          list.find((f) => f.id === student?.filiere_id) ||
          list.find((f) => String(f.id) === String(selection?.filiereId)) ||
          list[0]
        setFiliereId(preferred ? String(preferred.id) : '')
      } catch (err) {
        if (!cancelled) setError(err.message)
      } finally {
        if (!cancelled) setBusy(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [token, level, student?.filiere_id, selection?.filiereId])

  const selectedFiliere = useMemo(
    () => filieres.find((f) => String(f.id) === String(filiereId)),
    [filieres, filiereId],
  )

  if (loading) return <p className="p-8 text-center text-ist-500">Chargement…</p>
  if (!student) return <Navigate to="/login" replace />

  function confirm() {
    if (!selectedFiliere) {
      setError('Choisissez une filière')
      return
    }
    setSelection({
      level: selectedFiliere.level || level,
      filiereId: selectedFiliere.id,
      filiereName: selectedFiliere.name,
    })
    navigate('/schedule')
  }

  return (
    <div className="flex min-h-[calc(100dvh-64px)] flex-col">
      <main className="mx-auto w-full max-w-xl flex-1 px-4 py-10">
        <div className="mb-8">
          <p className="text-sm font-semibold uppercase tracking-wider text-gold-600">
            Étape 2 / 3
          </p>
          <h1 className="mt-1 font-display text-3xl font-extrabold text-ist-600 dark:text-white">
            Votre parcours
          </h1>
          <p className="mt-2 text-ist-500 dark:text-ist-300">
            Bonjour {student.first_name}, sélectionnez votre année et votre filière pour
            afficher l&apos;emploi du temps IST Wayalghin.
          </p>
        </div>

        <div className="space-y-6 rounded-3xl border border-ist-100 bg-white p-6 shadow-lg shadow-ist-900/5 dark:border-ist-700 dark:bg-ist-800/70 sm:p-8">
          <fieldset>
            <legend className="mb-3 font-display text-sm font-bold uppercase tracking-wide text-ist-600 dark:text-ist-200">
              Année / niveau
            </legend>
            <div className="grid grid-cols-3 gap-2 sm:grid-cols-5">
              {LEVELS.map((l) => {
                const active = level === l
                return (
                  <button
                    key={l}
                    type="button"
                    onClick={() => setLevel(l)}
                    className={`rounded-2xl px-3 py-3 text-sm font-bold transition ${
                      active
                        ? 'bg-ist-600 text-gold-400 shadow-md'
                        : 'bg-ist-50 text-ist-600 hover:bg-ist-100 dark:bg-ist-900 dark:text-ist-200 dark:hover:bg-ist-700'
                    }`}
                  >
                    {l}
                  </button>
                )
              })}
            </div>
          </fieldset>

          <label className="block">
            <span className="mb-2 block font-display text-sm font-bold uppercase tracking-wide text-ist-600 dark:text-ist-200">
              Filière / branche
            </span>
            <select
              value={filiereId}
              onChange={(e) => setFiliereId(e.target.value)}
              disabled={busy || filieres.length === 0}
              className="w-full rounded-2xl border border-ist-200 bg-ist-50/50 px-4 py-3.5 text-base font-medium text-ist-800 outline-none ring-gold-400 focus:ring-2 dark:border-ist-600 dark:bg-ist-900 dark:text-ist-50"
            >
              {filieres.length === 0 && <option value="">Aucune filière pour ce niveau</option>}
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
            type="button"
            onClick={confirm}
            disabled={!filiereId || busy}
            className="w-full rounded-2xl bg-gold-400 py-3.5 font-display text-base font-bold text-ist-700 shadow-md transition hover:bg-gold-300 disabled:opacity-50"
          >
            Voir mon emploi du temps
          </button>
        </div>
      </main>
      <Footer />
    </div>
  )
}
