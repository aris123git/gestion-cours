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
          className="rounded-3xl border border-ist-100 bg-white p-4 shadow-md shadow-ist-900/5 dark:border-ist-700 dark:bg-ist-800/50"
        >
          <h3 className="mb-3 flex items-center gap-2 font-display text-lg font-bold text-ist-600 dark:text-ist-100">
            <span className="h-2 w-2 rounded-full bg-gold-400" />
            {day}
          </h3>
          {byDay[day].length === 0 ? (
            <p className="rounded-2xl border border-dashed border-ist-200 px-3 py-6 text-center text-sm text-ist-400 dark:border-ist-600">
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

export function PrintableTable({ courses, student, weekLabel, programme }) {
  return (
    <div className="hidden print:block">
      <h1 style={{ fontSize: 18, marginBottom: 4 }}>IST Wayalghin — Emploi du temps</h1>
      <p style={{ marginBottom: 12, fontSize: 12 }}>
        {student?.first_name} {student?.last_name} · {programme} · {weekLabel}
      </p>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 11 }}>
        <thead>
          <tr>
            {['Jour', 'Horaire', 'Matière', 'Enseignant', 'Salle', 'Groupe'].map((h) => (
              <th
                key={h}
                style={{
                  border: '1px solid #003366',
                  padding: 6,
                  textAlign: 'left',
                  background: '#003366',
                  color: '#f5c518',
                }}
              >
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
              <td
                style={{
                  border: '1px solid #ccc',
                  padding: 6,
                  borderLeft: `3px solid ${subjectColor(c.subject).border}`,
                }}
              >
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
