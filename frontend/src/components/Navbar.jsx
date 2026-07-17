import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useTheme } from '../context/ThemeContext'

export default function Navbar({ onOpenNotifications }) {
  const { student, logout } = useAuth()
  const { dark, toggle } = useTheme()

  return (
    <header className="no-print sticky top-0 z-40 border-b border-brand-200/60 bg-white/80 backdrop-blur-md dark:border-brand-700/50 dark:bg-brand-900/80">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3">
        <Link to={student ? '/dashboard' : '/'} className="flex items-center gap-2.5">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-600 text-white shadow-md shadow-brand-600/25">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden>
              <path d="M3 19 L12 4 L21 19 Z" fill="currentColor" opacity="0.95" />
            </svg>
          </span>
          <span className="font-display text-xl font-semibold tracking-tight text-brand-700 dark:text-brand-100">
            GestionCours
          </span>
        </Link>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={toggle}
            className="rounded-xl px-3 py-2 text-sm text-brand-700 transition hover:bg-brand-100 dark:text-brand-100 dark:hover:bg-brand-800"
            aria-label="Basculer le thème"
          >
            {dark ? 'Clair' : 'Sombre'}
          </button>
          {student && (
            <>
              <button
                type="button"
                onClick={onOpenNotifications}
                className="rounded-xl px-3 py-2 text-sm text-brand-700 transition hover:bg-brand-100 dark:text-brand-100 dark:hover:bg-brand-800"
              >
                Alertes
              </button>
              <button
                type="button"
                onClick={logout}
                className="rounded-xl bg-brand-600 px-3 py-2 text-sm font-medium text-white shadow-sm transition hover:bg-brand-700"
              >
                Déconnexion
              </button>
            </>
          )}
        </div>
      </div>
    </header>
  )
}
