import { Link, Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { API_BASE, isApiConfiguredForProduction } from '../api'
import Footer from '../components/Footer'

export default function Landing() {
  const { student, loading } = useAuth()
  if (!loading && student) return <Navigate to="/select" replace />
  const apiReady = isApiConfiguredForProduction()

  return (
    <div className="flex min-h-[calc(100dvh-64px)] flex-col">
      <main className="relative flex-1 overflow-hidden">
        {/* Full-bleed campus atmosphere */}
        <div
          className="absolute inset-0 bg-cover bg-center"
          style={{ backgroundImage: 'url(/ist-logo.jpeg)' }}
          aria-hidden
        />
        <div className="absolute inset-0 bg-gradient-to-r from-ist-700/95 via-ist-600/90 to-ist-600/70" />
        <div
          className="pointer-events-none absolute inset-0 opacity-20"
          style={{
            backgroundImage:
              'radial-gradient(circle at 70% 30%, #f5c51855 0%, transparent 40%)',
          }}
        />

        <section className="relative mx-auto flex max-w-6xl flex-col justify-center gap-6 px-4 py-20 md:min-h-[72dvh] md:py-28">
          <img
            src="/ist-logo.jpeg"
            alt="Logo IST Wayalghin"
            className="h-24 w-24 rounded-full object-cover shadow-2xl ring-4 ring-gold-400 md:h-28 md:w-28"
          />
          <p className="font-display text-5xl font-extrabold tracking-tight text-white md:text-7xl">
            IST
          </p>
          <p className="font-display text-xl font-semibold text-gold-400 md:text-2xl">
            Campus de Wayalghin
          </p>
          <h1 className="max-w-xl text-lg font-medium text-ist-100 md:text-xl">
            Pour l&apos;excellence — consultez votre emploi du temps en ligne.
          </h1>
          <p className="max-w-lg text-sm text-ist-200 md:text-base">
            Connectez-vous, choisissez votre année et votre filière, puis visualisez
            votre planning de la semaine.
          </p>

          {!apiReady && (
            <div className="max-w-lg rounded-2xl border border-amber-300/80 bg-amber-50/95 px-4 py-3 text-sm text-amber-950">
              API non configurée sur Netlify. Définissez <code>VITE_API_URL</code> puis redéployez.
              (valeur actuelle : <code>{API_BASE}</code>)
            </div>
          )}

          <div className="flex flex-wrap gap-3 pt-2">
            <Link
              to="/register"
              className="rounded-2xl bg-gold-400 px-7 py-3.5 text-base font-bold text-ist-700 shadow-lg shadow-black/20 transition hover:-translate-y-0.5 hover:bg-gold-300"
            >
              Créer un compte
            </Link>
            <Link
              to="/login"
              className="rounded-2xl border border-white/40 bg-white/10 px-7 py-3.5 text-base font-semibold text-white backdrop-blur transition hover:bg-white/20"
            >
              Se connecter
            </Link>
          </div>
        </section>
      </main>

      <section id="comment" className="mx-auto max-w-6xl px-4 py-14">
        <h2 className="mb-8 font-display text-2xl font-bold text-ist-600 dark:text-white">
          Trois étapes
        </h2>
        <ol className="grid gap-6 md:grid-cols-3">
          {[
            { n: '1', t: 'Créer un compte', d: 'Inscrivez-vous avec votre numéro d’étudiant, puis connectez-vous.' },
            { n: '2', t: 'Année & filière', d: 'Choisissez votre niveau (L1, L2…) et votre branche.' },
            { n: '3', t: 'Planning + PDF', d: 'Consultez la semaine et téléchargez l’emploi du temps en PDF.' },
          ].map((step) => (
            <li key={step.n} className="relative pl-14">
              <span className="absolute left-0 top-0 flex h-10 w-10 items-center justify-center rounded-full bg-ist-600 font-display text-lg font-bold text-gold-400">
                {step.n}
              </span>
              <h3 className="font-display text-lg font-bold text-ist-600 dark:text-ist-100">{step.t}</h3>
              <p className="mt-1 text-sm leading-relaxed text-ist-500 dark:text-ist-300">{step.d}</p>
            </li>
          ))}
        </ol>
      </section>

      <Footer />
    </div>
  )
}
