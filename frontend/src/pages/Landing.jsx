import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { Navigate } from 'react-router-dom'
import { API_BASE, isApiConfiguredForProduction } from '../api'

export default function Landing() {
  const { student, loading } = useAuth()
  if (!loading && student) return <Navigate to="/dashboard" replace />
  const apiReady = isApiConfiguredForProduction()

  return (
    <main className="relative min-h-[calc(100dvh-64px)] overflow-hidden">
      {/* Atmosphere */}
      <div
        className="pointer-events-none absolute inset-0 opacity-40 dark:opacity-20"
        style={{
          backgroundImage:
            'radial-gradient(circle at 20% 20%, #7eb6ff55 0%, transparent 45%), radial-gradient(circle at 80% 60%, #1e4d8c22 0%, transparent 40%)',
        }}
      />
      <div
        className="pointer-events-none absolute inset-0 opacity-[0.35] dark:opacity-[0.15]"
        style={{
          backgroundImage:
            'url("data:image/svg+xml,%3Csvg width=\'60\' height=\'60\' viewBox=\'0 0 60 60\' xmlns=\'http://www.w3.org/2000/svg\'%3E%3Cg fill=\'none\' fill-rule=\'evenodd\'%3E%3Cg fill=\'%231e4d8c\' fill-opacity=\'0.08\'%3E%3Cpath d=\'M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z\'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")',
        }}
      />

      <section className="relative mx-auto flex max-w-6xl flex-col items-start justify-center gap-8 px-4 py-20 md:min-h-[70dvh] md:py-28">
        <p className="animate-fade-in font-display text-4xl font-bold tracking-tight text-brand-600 dark:text-brand-300 md:text-6xl lg:text-7xl">
          GestionCours
        </p>
        <h1 className="max-w-2xl text-2xl font-medium leading-snug text-brand-800 dark:text-brand-50 md:text-3xl">
          Votre emploi du temps universitaire, toujours à jour.
        </h1>
        <p className="max-w-xl text-base text-brand-700/80 dark:text-brand-200/80 md:text-lg">
          Connectez-vous avec votre numéro d&apos;étudiant pour consulter la semaine en cours,
          filtrer par filière et télécharger votre planning en PDF.
        </p>
        {!apiReady && (
          <div className="max-w-xl rounded-2xl border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-900 dark:border-amber-600 dark:bg-amber-900/40 dark:text-amber-100">
            Site Netlify détecté, mais l’API n’est pas configurée (<code>VITE_API_URL</code> vaut
            encore <code>{API_BASE}</code>). Hébergez le backend FastAPI, définissez{' '}
            <code>VITE_API_URL</code> dans Netlify, puis redéployez.
          </div>
        )}
        <div className="flex flex-wrap gap-3">
          <Link
            to="/login"
            className="rounded-2xl bg-brand-600 px-6 py-3.5 text-base font-semibold text-white shadow-lg shadow-brand-600/30 transition hover:-translate-y-0.5 hover:bg-brand-700"
          >
            Se connecter
          </Link>
          <a
            href="#apropos"
            className="rounded-2xl border border-brand-300 bg-white/70 px-6 py-3.5 text-base font-medium text-brand-700 backdrop-blur transition hover:bg-white dark:border-brand-600 dark:bg-brand-800/50 dark:text-brand-100"
          >
            En savoir plus
          </a>
        </div>
      </section>

      <section id="apropos" className="relative mx-auto max-w-6xl px-4 pb-24">
        <div className="grid gap-6 md:grid-cols-3">
          {[
            {
              title: 'Toujours synchronisé',
              text: 'Dès qu’un administrateur met à jour le planning, votre espace étudiant reflète les changements.',
            },
            {
              title: 'Mobile & hors ligne',
              text: 'Installez l’application (PWA) et consultez le dernier emploi du temps même sans connexion.',
            },
            {
              title: 'PDF & impression',
              text: 'Téléchargez ou imprimez votre semaine en un clic, avec un rendu clair et lisible.',
            },
          ].map((item) => (
            <div
              key={item.title}
              className="rounded-3xl bg-white/80 p-6 shadow-md shadow-brand-900/5 backdrop-blur dark:bg-brand-800/50"
            >
              <h2 className="mb-2 font-display text-xl font-semibold text-brand-700 dark:text-brand-100">
                {item.title}
              </h2>
              <p className="text-sm leading-relaxed text-brand-700/75 dark:text-brand-200/75">{item.text}</p>
            </div>
          ))}
        </div>
      </section>

      <style>{`
        @keyframes fade-in {
          from { opacity: 0; transform: translateY(12px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .animate-fade-in { animation: fade-in 0.7s ease-out both; }
      `}</style>
    </main>
  )
}
