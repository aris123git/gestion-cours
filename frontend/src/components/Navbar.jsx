import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useTheme } from '../context/ThemeContext'
import { useSelection } from '../context/SelectionContext'

export default function Navbar({ onOpenNotifications }) {
  const { student, logout } = useAuth()
  const { dark, toggle } = useTheme()
  const { clearSelection } = useSelection()

  function handleLogout() {
    clearSelection()
    logout()
  }

  return (
    <header className="no-print sticky top-0 z-40 border-b border-ist-200/70 bg-white/90 backdrop-blur-md dark:border-ist-700 dark:bg-ist-900/90">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-3 px-4 py-2.5">
        <Link to={student ? '/select' : '/'} className="flex items-center gap-3 min-w-0">
          <img
            src="/ist-logo.jpeg"
            alt="IST Wayalghin"
            className="h-11 w-11 shrink-0 rounded-full object-cover ring-2 ring-gold-400/80"
          />
          <div className="min-w-0 leading-tight">
            <p className="font-display text-lg font-extrabold tracking-tight text-ist-600 dark:text-white">
              IST
            </p>
            <p className="truncate text-xs font-medium text-ist-400 dark:text-ist-300">
              Campus de Wayalghin
            </p>
          </div>
        </Link>

        <div className="flex items-center gap-1.5 sm:gap-2">
          <button
            type="button"
            onClick={toggle}
            className="rounded-xl px-2.5 py-2 text-sm text-ist-600 transition hover:bg-ist-100 dark:text-ist-100 dark:hover:bg-ist-800"
            aria-label="Basculer le thème"
          >
            {dark ? 'Clair' : 'Sombre'}
          </button>
          {student && (
            <>
              <Link
                to="/select"
                className="hidden rounded-xl px-3 py-2 text-sm text-ist-600 transition hover:bg-ist-100 sm:inline dark:text-ist-100 dark:hover:bg-ist-800"
              >
                Filière
              </Link>
              <button
                type="button"
                onClick={onOpenNotifications}
                className="rounded-xl px-3 py-2 text-sm text-ist-600 transition hover:bg-ist-100 dark:text-ist-100 dark:hover:bg-ist-800"
              >
                Alertes
              </button>
              <button
                type="button"
                onClick={handleLogout}
                className="rounded-xl bg-ist-600 px-3 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-ist-700"
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
