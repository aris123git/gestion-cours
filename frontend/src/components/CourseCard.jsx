import { formatTime, subjectColor } from '../api'

export default function CourseCard({ course, compact = false }) {
  const colors = subjectColor(course.subject)
  return (
    <article
      className={`rounded-2xl border-l-4 bg-white p-4 shadow-sm shadow-brand-900/5 transition hover:-translate-y-0.5 hover:shadow-md dark:bg-brand-800/60 ${
        compact ? 'p-3' : ''
      }`}
      style={{ borderLeftColor: colors.border }}
    >
      <div className="mb-2 flex items-start justify-between gap-2">
        <h3
          className={`font-semibold leading-snug ${compact ? 'text-sm' : 'text-base'}`}
          style={{ color: colors.text }}
        >
          {course.subject}
        </h3>
        <span className="shrink-0 rounded-lg bg-brand-50 px-2 py-0.5 text-xs font-medium text-brand-700 dark:bg-brand-900 dark:text-brand-200">
          {formatTime(course.start_time)} – {formatTime(course.end_time)}
        </span>
      </div>
      <dl className={`space-y-1 ${compact ? 'text-xs' : 'text-sm'} text-brand-700/80 dark:text-brand-200/80`}>
        <div className="flex gap-2">
          <dt className="sr-only">Enseignant</dt>
          <dd>{course.teacher}</dd>
        </div>
        {course.room && (
          <div className="flex gap-2">
            <dt className="opacity-60">Salle</dt>
            <dd className="font-medium">{course.room}</dd>
          </div>
        )}
        {course.group_tc && (
          <div className="flex gap-2">
            <dt className="opacity-60">Groupe</dt>
            <dd>{course.group_tc}</dd>
          </div>
        )}
      </dl>
    </article>
  )
}
