import { formatTime, subjectColor } from '../api'

export default function CourseCard({ course, compact = false }) {
  const colors = subjectColor(course.subject)
  return (
    <article
      className={`rounded-2xl border border-ist-100 border-l-4 bg-white shadow-sm shadow-ist-900/5 transition hover:-translate-y-0.5 hover:shadow-md dark:border-ist-700 dark:bg-ist-800/70 ${
        compact ? 'p-3' : 'p-4'
      }`}
      style={{ borderLeftColor: colors.border }}
    >
      <div className="mb-2 flex items-start justify-between gap-2">
        <h3
          className={`font-display font-bold leading-snug ${compact ? 'text-sm' : 'text-base'}`}
          style={{ color: colors.text }}
        >
          {course.subject}
        </h3>
        <span className="shrink-0 rounded-lg bg-ist-50 px-2 py-0.5 text-xs font-semibold text-ist-600 dark:bg-ist-900 dark:text-ist-200">
          {formatTime(course.start_time)} – {formatTime(course.end_time)}
        </span>
      </div>
      <dl className={`space-y-1 ${compact ? 'text-xs' : 'text-sm'} text-ist-600/85 dark:text-ist-200/85`}>
        <div>
          <dt className="sr-only">Enseignant</dt>
          <dd>{course.teacher}</dd>
        </div>
        {course.room && (
          <div className="flex gap-2">
            <dt className="opacity-60">Salle</dt>
            <dd className="font-semibold">{course.room}</dd>
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
