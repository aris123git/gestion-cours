import { useMemo } from 'react'
import CourseCard from './CourseCard'
import { formatTime, subjectColor } from '../api'

const DAYS = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi']

export default function WeeklyGrid({ courses }) {
  const byDay = useMemo(() => {
    const map = Object.fromEntries(DAYS.map((d) => [d, []]))
    for (const c of courses) {
      if (map[c.day]) map[c.day].push(c)
      else map[c.day] = [c]
    }
    for (const d of DAYS) {
      map[d].sort((a, b) => String(a.start_time).localeCompare(String(b.start_time)))
    }
    return map
  }, [courses])

  return (
    <div className="print-area grid gap-4 md:grid-cols-2 xl:grid-cols-3">
      {DAYS.map((day) => (
        <section
          key={day}
          className="rounded-3xl bg-white/80 p-4 shadow-md shadow-brand-900/5 dark:bg-brand-800/50"
        >
          <h3 className="mb-3 font-display text-lg font-semibold text-brand-700 dark:text-brand-100">
            {day}
          </h3>
          {byDay[day].length === 0 ? (
            <p className="rounded-2xl border border-dashed border-brand-200 px-3 py-6 text-center text-sm text-brand-500 dark:border-brand-600 dark:text-brand-300">
              Aucun cours
            </p>
          ) : (
            <div className="space-y-3">
              {byDay[day].map((c) => (
                <CourseCard key={c.id} course={c} compact />
              ))}
            </div>
          )}
        </section>
      ))}
    </div>
  )
}

/** Simple printable / PDF-friendly table */
export function PrintableTable({ courses, student, weekLabel }) {
  return (
    <div className="hidden print:block">
      <h1 style={{ fontSize: 18, marginBottom: 4 }}>GestionCours — Emploi du temps</h1>
      <p style={{ marginBottom: 12, fontSize: 12 }}>
        {student?.first_name} {student?.last_name} · {student?.filiere_name} ({student?.level}) ·{' '}
        {weekLabel}
      </p>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 11 }}>
        <thead>
          <tr>
            {['Jour', 'Horaire', 'Matière', 'Enseignant', 'Salle', 'Groupe'].map((h) => (
              <th key={h} style={{ border: '1px solid #ccc', padding: 6, textAlign: 'left' }}>
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {courses.map((c) => (
            <tr key={c.id}>
              <td style={{ border: '1px solid #ccc', padding: 6 }}>{c.day}</td>
              <td style={{ border: '1px solid #ccc', padding: 6 }}>
                {formatTime(c.start_time)}–{formatTime(c.end_time)}
              </td>
              <td style={{ border: '1px solid #ccc', padding: 6, borderLeft: `3px solid ${subjectColor(c.subject).border}` }}>
                {c.subject}
              </td>
              <td style={{ border: '1px solid #ccc', padding: 6 }}>{c.teacher}</td>
              <td style={{ border: '1px solid #ccc', padding: 6 }}>{c.room || '—'}</td>
              <td style={{ border: '1px solid #ccc', padding: 6 }}>{c.group_tc || '—'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
