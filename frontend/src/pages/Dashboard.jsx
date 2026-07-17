import { useCallback, useEffect, useMemo, useState } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { api, formatWeekLabel, mondayOf, toISODate, todayNameFr } from '../api'
import CourseCard from '../components/CourseCard'
import WeeklyGrid, { PrintableTable } from '../components/WeeklyGrid'

function shiftWeek(isoMonday, deltaWeeks) {
  const d = new Date(isoMonday + 'T00:00:00')
  d.setDate(d.getDate() + deltaWeeks * 7)
  return toISODate(d)
}

export default function Dashboard({ notificationsOpen, setNotificationsOpen }) {
  const { token, student, loading } = useAuth()
  const [week, setWeek] = useState(() => toISODate(mondayOf()))
  const [filiereId, setFiliereId] = useState('')
  const [level, setLevel] = useState('')
  const [search, setSearch] = useState('')
  const [courses, setCourses] = useState([])
  const [filieres, setFilieres] = useState([])
  const [notifications, setNotifications] = useState([])
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    if (student?.filiere_id) setFiliereId(String(student.filiere_id))
    if (student?.level) setLevel(student.level)
  }, [student])

  const load = useCallback(async () => {
    if (!token) return
    setBusy(true)
    setError('')
    try {
      const [sched, fils, notifs] = await Promise.all([
        api.getSchedule(token, {
          week,
          filiere_id: filiereId || undefined,
          level: level || undefined,
          search: search || undefined,
        }),
        api.getFilieres(token, level || undefined),
        api.getNotifications(token),
      ])
      setCourses(sched)
      setFilieres(fils)
      setNotifications(notifs)
      // Cache for offline
      try {
        localStorage.setItem(
          `gestioncours_cache_${week}_${filiereId}`,
          JSON.stringify(sched),
        )
      } catch {
        /* ignore quota */
      }
    } catch (err) {
      // Try offline cache
      try {
        const cached = localStorage.getItem(`gestioncours_cache_${week}_${filiereId}`)
        if (cached) {
          setCourses(JSON.parse(cached))
          setError('Mode hors ligne — affichage du cache local')
        } else {
          setError(err.message)
        }
      } catch {
        setError(err.message)
      }
    } finally {
      setBusy(false)
    }
  }, [token, week, filiereId, level, search])

  useEffect(() => {
    load()
  }, [load])

  // Poll for timetable change notifications
  useEffect(() => {
    if (!token) return undefined
    const id = setInterval(async () => {
      try {
        const notifs = await api.getNotifications(token, true)
        if (notifs.length) {
          setNotifications((prev) => {
            const ids = new Set(prev.map((n) => n.id))
            const merged = [...notifs.filter((n) => !ids.has(n.id)), ...prev]
            return merged
          })
          load()
        }
      } catch {
        /* offline */
      }
    }, 45000)
    return () => clearInterval(id)
  }, [token, load])

  const todayCourses = useMemo(() => {
    const day = todayNameFr()
    return courses.filter((c) => c.day === day)
  }, [courses])

  const weekLabel = formatWeekLabel(week)
  const unread = notifications.filter((n) => !n.is_read).length

  async function markRead(id) {
    try {
      await api.markNotificationRead(token, id)
      setNotifications((prev) => prev.map((n) => (n.id === id ? { ...n, is_read: true } : n)))
    } catch {
      /* ignore */
    }
  }

  function downloadPdf() {
    // Print-to-PDF via browser — reliable without extra deps
    window.print()
  }

  if (loading) {
    return <p className="p-8 text-center text-brand-600">Chargement…</p>
  }
  if (!student) return <Navigate to="/login" replace />

  return (
    <main className="mx-auto max-w-6xl px-4 py-8">
      {/* Profile header */}
      <section className="mb-8 animate-slide rounded-3xl bg-gradient-to-br from-brand-600 to-brand-800 p-6 text-white shadow-xl shadow-brand-600/20 md:p-8">
        <p className="text-sm font-medium text-brand-200">Espace étudiant</p>
        <h1 className="mt-1 font-display text-3xl font-bold md:text-4xl">
          {student.first_name} {student.last_name}
        </h1>
        <div className="mt-4 flex flex-wrap gap-3 text-sm">
          <span className="rounded-xl bg-white/15 px-3 py-1.5 backdrop-blur">
            {student.filiere_name || 'Programme'}
          </span>
          <span className="rounded-xl bg-white/15 px-3 py-1.5 backdrop-blur">Niveau {student.level}</span>
          <span className="rounded-xl bg-white/15 px-3 py-1.5 backdrop-blur">Semaine {weekLabel}</span>
          {unread > 0 && (
            <button
              type="button"
              onClick={() => setNotificationsOpen(true)}
              className="no-print rounded-xl bg-amber-400/90 px-3 py-1.5 font-medium text-brand-900"
            >
              {unread} mise(s) à jour
            </button>
          )}
        </div>
      </section>

      {/* Filters */}
      <section className="no-print mb-6 grid gap-3 rounded-3xl bg-white/80 p-4 shadow-md shadow-brand-900/5 dark:bg-brand-800/50 sm:grid-cols-2 lg:grid-cols-5">
        <label className="block text-sm">
          <span className="mb-1 block text-brand-600 dark:text-brand-300">Semaine</span>
          <div className="flex gap-1">
            <button
              type="button"
              className="rounded-xl bg-brand-100 px-3 py-2 dark:bg-brand-700"
              onClick={() => setWeek((w) => shiftWeek(w, -1))}
            >
              ◀
            </button>
            <input
              type="date"
              value={week}
              onChange={(e) => setWeek(toISODate(mondayOf(new Date(e.target.value))))}
              className="w-full rounded-xl border border-brand-200 bg-transparent px-2 py-2 dark:border-brand-600"
            />
            <button
              type="button"
              className="rounded-xl bg-brand-100 px-3 py-2 dark:bg-brand-700"
              onClick={() => setWeek((w) => shiftWeek(w, 1))}
            >
              ▶
            </button>
          </div>
        </label>
        <label className="block text-sm">
          <span className="mb-1 block text-brand-600 dark:text-brand-300">Niveau</span>
          <select
            value={level}
            onChange={(e) => setLevel(e.target.value)}
            className="w-full rounded-xl border border-brand-200 bg-transparent px-3 py-2 dark:border-brand-600"
          >
            <option value="">Tous</option>
            {['L1', 'L2', 'L3', 'Master', 'Doctorat'].map((l) => (
              <option key={l} value={l}>
                {l}
              </option>
            ))}
          </select>
        </label>
        <label className="block text-sm">
          <span className="mb-1 block text-brand-600 dark:text-brand-300">Programme</span>
          <select
            value={filiereId}
            onChange={(e) => setFiliereId(e.target.value)}
            className="w-full rounded-xl border border-brand-200 bg-transparent px-3 py-2 dark:border-brand-600"
          >
            {filieres.map((f) => (
              <option key={f.id} value={f.id}>
                {f.level} — {f.name}
              </option>
            ))}
          </select>
        </label>
        <label className="block text-sm sm:col-span-2 lg:col-span-2">
          <span className="mb-1 block text-brand-600 dark:text-brand-300">Recherche</span>
          <input
            type="search"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Matière, enseignant, salle…"
            className="w-full rounded-xl border border-brand-200 bg-transparent px-3 py-2 dark:border-brand-600"
          />
        </label>
      </section>

      <div className="no-print mb-6 flex flex-wrap gap-2">
        <button
          type="button"
          onClick={downloadPdf}
          className="rounded-2xl bg-brand-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-brand-700"
        >
          Télécharger / Imprimer PDF
        </button>
        <button
          type="button"
          onClick={load}
          className="rounded-2xl border border-brand-300 bg-white px-4 py-2.5 text-sm font-medium text-brand-700 dark:border-brand-600 dark:bg-brand-800 dark:text-brand-100"
        >
          Actualiser {busy ? '…' : ''}
        </button>
      </div>

      {error && (
        <p className="no-print mb-4 rounded-2xl bg-amber-50 px-4 py-3 text-sm text-amber-800 dark:bg-amber-900/40 dark:text-amber-100">
          {error}
        </p>
      )}

      {/* Today */}
      <section className="mb-10">
        <h2 className="mb-4 font-display text-2xl font-semibold text-brand-700 dark:text-brand-100">
          Cours d&apos;aujourd&apos;hui
        </h2>
        {todayCourses.length === 0 ? (
          <p className="rounded-3xl border border-dashed border-brand-200 bg-white/50 px-4 py-10 text-center text-brand-500 dark:border-brand-600 dark:bg-brand-800/30">
            Pas de cours aujourd&apos;hui pour cette sélection.
          </p>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2">
            {todayCourses.map((c) => (
              <CourseCard key={c.id} course={c} />
            ))}
          </div>
        )}
      </section>

      {/* Full week */}
      <section>
        <h2 className="mb-4 font-display text-2xl font-semibold text-brand-700 dark:text-brand-100">
          Semaine complète
        </h2>
        <WeeklyGrid courses={courses} />
      </section>

      <PrintableTable courses={courses} student={student} weekLabel={weekLabel} />

      {/* Notifications drawer */}
      {notificationsOpen && (
        <div className="no-print fixed inset-0 z-50 flex justify-end bg-brand-900/40 backdrop-blur-sm">
          <button
            type="button"
            className="flex-1"
            aria-label="Fermer"
            onClick={() => setNotificationsOpen(false)}
          />
          <aside className="h-full w-full max-w-md overflow-y-auto bg-white p-6 shadow-2xl dark:bg-brand-900">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="font-display text-xl font-semibold">Notifications</h2>
              <button
                type="button"
                onClick={() => setNotificationsOpen(false)}
                className="rounded-xl px-3 py-1 text-sm hover:bg-brand-100 dark:hover:bg-brand-800"
              >
                Fermer
              </button>
            </div>
            {notifications.length === 0 ? (
              <p className="text-sm text-brand-500">Aucune notification.</p>
            ) : (
              <ul className="space-y-3">
                {notifications.map((n) => (
                  <li
                    key={n.id}
                    className={`rounded-2xl border p-4 ${
                      n.is_read
                        ? 'border-brand-100 opacity-70 dark:border-brand-700'
                        : 'border-brand-300 bg-brand-50 dark:border-brand-500 dark:bg-brand-800'
                    }`}
                  >
                    <p className="font-medium">{n.title}</p>
                    <p className="mt-1 text-sm text-brand-700/80 dark:text-brand-200/80">{n.message}</p>
                    <p className="mt-2 text-xs text-brand-500">
                      {new Date(n.created_at).toLocaleString('fr-FR')}
                    </p>
                    {!n.is_read && (
                      <button
                        type="button"
                        onClick={() => markRead(n.id)}
                        className="mt-2 text-xs font-semibold text-brand-600 underline"
                      >
                        Marquer comme lu
                      </button>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </aside>
        </div>
      )}

      <style>{`
        @keyframes slide {
          from { opacity: 0; transform: translateY(16px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .animate-slide { animation: slide 0.55s ease-out both; }
      `}</style>
    </main>
  )
}
