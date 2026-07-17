export default function Footer() {
  return (
    <footer className="no-print mt-auto border-t-4 border-gold-400 bg-ist-600 text-white">
      <div className="mx-auto flex max-w-6xl flex-col gap-3 px-4 py-5 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="font-display text-lg font-bold tracking-wide text-gold-400">
            Campus de Wayalghin
          </p>
          <p className="mt-0.5 text-sm text-ist-100">
            Route de Fada · 900 m de l&apos;échangeur de l&apos;Est
          </p>
        </div>
        <div className="text-sm sm:text-right">
          <p className="font-display text-xl font-bold text-gold-400">68 00 23 00</p>
          <p className="text-ist-200">IST — Pour l&apos;excellence</p>
        </div>
      </div>
    </footer>
  )
}
