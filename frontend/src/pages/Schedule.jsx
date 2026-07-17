import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useSelection } from '../context/SelectionContext'
import { api, formatWeekLabel, mondayOf, toISODate, todayNameFr } from '../api'
import CourseCard from '../components/CourseCard'
import WeeklyGrid, { PrintableTable } from '../components/WeeklyGrid'
import Footer from '../components/Footer'

function shiftWeek(isoMonday, deltaWeeks) {
  const d = new Date(isoMonday + 'T00:00:00')
  d.setDate(d.getDate() + deltaWeeks * 7)
  return toISODate(d)
}

export default function Schedule({ notificationsOpen, setNotificationsOpen }) {
  const { token, student, loading } = useAuth()
  const { selection } = useSelection()
  const [week, setWeek] = useState(() => toISODate(mondayOf()))
  const [search, setSearch] = useState('')
  const [courses, setCourses] = useState([])
  const [notifications, setNotifications] = useState([])
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [pdfBusy, setPdfBusy] = useState(false)

  const load = useCallback(async () => {
    if (!token || !selection?.filiereId) return
    setBusy(true)
    setError('')
    try {
      const [sched, notifs] = await Promise.all([
        api.getSchedule(token, {
          week,
          filiere_id: selection.filiereId,
          level: selection.level || undefined,
          search: search || undefined,
        }),
        api.getNotifications(token),
      ])
      setCourses(sched)
      setNotifications(notifs)
      try {
        localStorage.setItem(
          `ist_cache_${week}_${selection.filiereId}`,
          JSON.stringify(sched),
        )
      } catch {
        /* ignore */
      }
    } catch (err) {
      try {
        const cached = localStorage.getItem(`ist_cache_${week}_${selection.filiereId}`)
        if (cached) {
          setCourses(JSON.parse(cached))
          setError('Mode hors ligne — cache local')
        } else {
          setError(err.message)
        }
      } catch {
        setError(err.message)
      }
    } finally {
      setBusy(false)
    }
  }, [token, week, selection, search])

  useEffect(() => {
    load()
  }, [load])

  useEffect(() => {
    if (!token) return undefined
    const id = setInterval(async () => {
      try {
        const notifs = await api.getNotifications(token, true)
        if (notifs.length) {
          setNotifications((prev) => {
            const ids = new Set(prev.map((n) => n.id))
            return [...notifs.filter((n) => !ids.has(n.id)), ...prev]
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

  async function downloadPdf() {
    if (!token || !selection?.filiereId) return
    setPdfBusy(true)
    setError('')
    try {
      const blob = await api.downloadSchedulePdf(token, {
        week,
        filiereId: selection.filiereId,
      })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `EDT_IST_${selection.level}_${selection.filiereName}_${week}.pdf`.replace(
        /\s+/g,
        '_',
      )
      document.body.appendChild(a)
      a.click()
      a.remove()
      URL.revokeObjectURL(url)
    } catch (err) {
      setError(err.message || 'Téléchargement PDF impossible')
    } finally {
      setPdfBusy(false)
    }
  }

  if (loading) return <p className="p-8 text-center text-ist-500">Chargement…</p>
  if (!student) return <Navigate to="/login" replace />
  if (!selection?.filiereId) return <Navigate to="/select" replace />

  return (
    <div className="flex min-h-[calc(100dvh-64px)] flex-col">
      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-8">
        <section className="mb-8 overflow-hidden rounded-3xl bg-ist-600 text-white shadow-xl shadow-ist-600/25">
          <div className="flex flex-col gap-4 p-6 md:flex-row md:items-center md:justify-between md:p-8">
            <div>
              <p className="text-sm font-semibold text-gold-400">IST Wayalghin · Emploi du temps</p>
              <h1 className="mt-1 font-display text-3xl font-extrabold md:text-4xl">
                {student.first_name} {student.last_name}
              </h1>
              <div className="mt-3 flex flex-wrap gap-2 text-sm">
                <span className="rounded-xl bg-white/10 px-3 py-1.5">
                  {selection.level} — {selection.filiereName}
                </span>
                <span className="rounded-xl bg-white/10 px-3 py-1.5">Semaine {weekLabel}</span>
                {unread > 0 && (
                  <button
                    type="button"
                    onClick={() => setNotificationsOpen(true)}
                    className="no-print rounded-xl bg-gold-400 px-3 py-1.5 font-semibold text-ist-700"
                  >
                    {unread} alerte(s)
                  </button>
                )}
              </div>
            </div>
            <Link
              to="/select"
              className="no-print inline-flex self-start rounded-2xl border border-white/30 bg-white/10 px-4 py-2.5 text-sm font-semibold backdrop-blur transition hover:bg-white/20"
            >
              Changer d&apos;année / filière
            </Link>
          </div>
          <div className="h-1.5 bg-gold-400" />
        </section>

        <section className="no-print mb-6 grid gap-3 rounded-3xl border border-ist-100 bg-white p-4 shadow-md dark:border-ist-700 dark:bg-ist-800/60 sm:grid-cols-2 lg:grid-cols-3">
          <label className="block text-sm sm:col-span-1">
            <span className="mb-1 block font-semibold text-ist-600 dark:text-ist-300">Semaine</span>
            <div className="flex gap-1">
              <button
                type="button"
                className="rounded-xl bg-ist-100 px-3 py-2 font-bold text-ist-600 dark:bg-ist-700 dark:text-white"
                onClick={() => setWeek((w) => shiftWeek(w, -1))}
              >
                ◀
              </button>
              <input
                type="date"
                value={week}
                onChange={(e) => setWeek(toISODate(mondayOf(new Date(e.target.value))))}
                className="w-full rounded-xl border border-ist-200 bg-transparent px-2 py-2 dark:border-ist-600"
              />
              <button
                type="button"
                className="rounded-xl bg-ist-100 px-3 py-2 font-bold text-ist-600 dark:bg-ist-700 dark:text-white"
                onClick={() => setWeek((w) => shiftWeek(w, 1))}
              >
                ▶
              </button>
            </div>
          </label>
          <label className="block text-sm sm:col-span-1 lg:col-span-2">
            <span className="mb-1 block font-semibold text-ist-600 dark:text-ist-300">Recherche</span>
            <input
              type="search"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Matière, enseignant, salle…"
              className="w-full rounded-xl border border-ist-200 bg-transparent px-3 py-2 dark:border-ist-600"
            />
          </label>
        </section>

        <div className="no-print mb-6 flex flex-wrap gap-2">
          <button
            type="button"
            onClick={downloadPdf}
            disabled={pdfBusy}
            className="rounded-2xl bg-gold-400 px-4 py-2.5 text-sm font-bold text-ist-700 shadow-sm hover:bg-gold-300 disabled:opacity-60"
          >
            {pdfBusy ? 'PDF…' : 'Télécharger le PDF'}
          </button>
          <button
            type="button"
            onClick={() => window.print()}
            className="rounded-2xl border border-ist-300 bg-white px-4 py-2.5 text-sm font-semibold text-ist-600 dark:border-ist-600 dark:bg-ist-800 dark:text-ist-100"
          >
            Imprimer
          </button>
          <button
            type="button"
            onClick={load}
            className="rounded-2xl border border-ist-300 bg-white px-4 py-2.5 text-sm font-semibold text-ist-600 dark:border-ist-600 dark:bg-ist-800 dark:text-ist-100"
          >
            Actualiser {busy ? '…' : ''}
          </button>
        </div>

        {error && (
          <p className="no-print mb-4 rounded-2xl bg-amber-50 px-4 py-3 text-sm text-amber-900 dark:bg-amber-900/40 dark:text-amber-100">
            {error}
          </p>
        )}

        <section className="mb-10">
          <h2 className="mb-4 font-display text-2xl font-bold text-ist-600 dark:text-ist-100">
            Aujourd&apos;hui
          </h2>
          {todayCourses.length === 0 ? (
            <p className="rounded-3xl border border-dashed border-ist-200 bg-white/70 px-4 py-10 text-center text-ist-400 dark:border-ist-600 dark:bg-ist-800/30">
              Pas de cours aujourd&apos;hui pour {selection.filiereName}.
            </p>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2">
              {todayCourses.map((c) => (
                <CourseCard key={c.id} course={c} />
              ))}
            </div>
          )}
        </section>

        <section>
          <h2 className="mb-4 font-display text-2xl font-bold text-ist-600 dark:text-ist-100">
            Semaine complète
          </h2>
          <WeeklyGrid courses={courses} />
        </section>

        <PrintableTable
          courses={courses}
          student={student}
          weekLabel={weekLabel}
          programme={`${selection.level} — ${selection.filiereName}`}
        />

        {notificationsOpen && (
          <div className="no-print fixed inset-0 z-50 flex justify-end bg-ist-900/40 backdrop-blur-sm">
            <button
              type="button"
              className="flex-1"
              aria-label="Fermer"
              onClick={() => setNotificationsOpen(false)}
            />
            <aside className="h-full w-full max-w-md overflow-y-auto bg-white p-6 shadow-2xl dark:bg-ist-900">
              <div className="mb-4 flex items-center justify-between">
                <h2 className="font-display text-xl font-bold text-ist-600 dark:text-white">
                  Notifications
                </h2>
                <button
                  type="button"
                  onClick={() => setNotificationsOpen(false)}
                  className="rounded-xl px-3 py-1 text-sm hover:bg-ist-100 dark:hover:bg-ist-800"
                >
                  Fermer
                </button>
              </div>
              {notifications.length === 0 ? (
                <p className="text-sm text-ist-400">Aucune notification.</p>
              ) : (
                <ul className="space-y-3">
                  {notifications.map((n) => (
                    <li
                      key={n.id}
                      className={`rounded-2xl border p-4 ${
                        n.is_read
                          ? 'border-ist-100 opacity-70 dark:border-ist-700'
                          : 'border-gold-400 bg-ist-50 dark:bg-ist-800'
                      }`}
                    >
                      <p className="font-semibold text-ist-700 dark:text-ist-100">{n.title}</p>
                      <p className="mt-1 text-sm text-ist-500 dark:text-ist-300">{n.message}</p>
                      <p className="mt-2 text-xs text-ist-400">
                        {new Date(n.created_at).toLocaleString('fr-FR')}
                      </p>
                      {!n.is_read && (
                        <button
                          type="button"
                          onClick={() => markRead(n.id)}
                          className="mt-2 text-xs font-bold text-ist-600 underline"
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
      </main>
      <Footer />
    </div>
  )
}
