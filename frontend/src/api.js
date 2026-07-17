/**
 * API base URL.
 * - Local Docker / Vite proxy: `/api`
 * - Netlify production: set `VITE_API_URL` to your public FastAPI URL
 *   (e.g. https://gestion-cours-api.onrender.com) in Netlify env vars, then redeploy.
 */
function resolveApiBase() {
  const raw = (import.meta.env.VITE_API_URL || '/api').trim().replace(/\/$/, '')
  return raw || '/api'
}

export const API_BASE = resolveApiBase()

export function isApiConfiguredForProduction() {
  // Relative /api only works behind a reverse proxy (Docker/nginx), not on bare Netlify.
  if (typeof window === 'undefined') return true
  const host = window.location.hostname
  const isNetlify = host.endsWith('netlify.app') || host.endsWith('netlify.com')
  if (!isNetlify) return true
  return API_BASE.startsWith('http://') || API_BASE.startsWith('https://')
}

async function request(path, { method = 'GET', body, token, headers = {} } = {}) {
  const opts = {
    method,
    headers: {
      Accept: 'application/json',
      ...headers,
    },
  }
  if (body !== undefined) {
    opts.headers['Content-Type'] = 'application/json'
    opts.body = JSON.stringify(body)
  }
  if (token) {
    opts.headers.Authorization = `Bearer ${token}`
  }

  let res
  try {
    res = await fetch(`${API_BASE}${path}`, opts)
  } catch {
    const err = new Error(
      isApiConfiguredForProduction()
        ? 'Impossible de joindre le serveur API. Vérifiez que le backend est démarré.'
        : 'API non configurée pour Netlify. Définissez VITE_API_URL (URL du backend) dans les variables d’environnement Netlify, puis redéployez.',
    )
    err.status = 0
    throw err
  }
  if (res.status === 204) return null

  let data = null
  const text = await res.text()
  if (text) {
    try {
      data = JSON.parse(text)
    } catch {
      data = { detail: text }
    }
  }

  if (!res.ok) {
    const detail = data?.detail
    const message = typeof detail === 'string' ? detail : detail?.[0]?.msg || 'Une erreur est survenue'
    const err = new Error(message)
    err.status = res.status
    err.data = data
    throw err
  }
  return data
}

export const api = {
  login: (student_number, password) =>
    request('/login', { method: 'POST', body: { student_number, password } }),

  register: (payload) => request('/register', { method: 'POST', body: payload }),

  getPublicFilieres: (level) => {
    const qs = level ? `?level=${encodeURIComponent(level)}` : ''
    return request(`/public/filieres${qs}`)
  },

  getStudent: (token) => request('/student', { token }),

  getSchedule: (token, params = {}) => {
    const qs = new URLSearchParams()
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== '') qs.set(k, v)
    })
    const q = qs.toString()
    return request(`/schedule${q ? `?${q}` : ''}`, { token })
  },

  getScheduleWeek: (token, weekDate, filiereId) => {
    const qs = filiereId ? `?filiere_id=${filiereId}` : ''
    return request(`/schedule/week/${weekDate}${qs}`, { token })
  },

  /** Download timetable PDF (returns a Blob). */
  downloadSchedulePdf: async (token, { week, filiereId } = {}) => {
    const qs = new URLSearchParams()
    if (week) qs.set('week', week)
    if (filiereId) qs.set('filiere_id', filiereId)
    const q = qs.toString()
    const res = await fetch(`${API_BASE}/schedule/pdf${q ? `?${q}` : ''}`, {
      headers: { Authorization: `Bearer ${token}`, Accept: 'application/pdf' },
    })
    if (!res.ok) {
      let message = 'Téléchargement PDF impossible'
      try {
        const data = await res.json()
        message = data?.detail || message
      } catch {
        /* ignore */
      }
      throw new Error(message)
    }
    return res.blob()
  },

  getFilieres: (token, level) => {
    const qs = level ? `?level=${encodeURIComponent(level)}` : ''
    return request(`/filieres${qs}`, { token })
  },

  getNotifications: (token, unreadOnly = false) =>
    request(`/notifications${unreadOnly ? '?unread_only=true' : ''}`, { token }),

  markNotificationRead: (token, id) =>
    request(`/notifications/${id}/read`, { method: 'POST', token }),
}

/** Subject colors — IST navy/gold family + distinct accents */
export function subjectColor(subject) {
  const palette = [
    { bg: '#e4eef7', border: '#003366', text: '#003366' },
    { bg: '#d9ecf8', border: '#0073bb', text: '#005f9a' },
    { bg: '#fff4cc', border: '#d4a017', text: '#7a5a00' },
    { bg: '#e8f5e9', border: '#2e7d32', text: '#1b5e20' },
    { bg: '#fce8e6', border: '#c62828', text: '#8e0000' },
    { bg: '#f3e5f5', border: '#6a1b9a', text: '#4a148c' },
    { bg: '#e0f2f1', border: '#00695c', text: '#004d40' },
    { bg: '#fff3e0', border: '#ef6c00', text: '#e65100' },
  ]
  let hash = 0
  const s = subject || '?'
  for (let i = 0; i < s.length; i++) hash = (hash * 31 + s.charCodeAt(i)) >>> 0
  return palette[hash % palette.length]
}

export function mondayOf(d = new Date()) {
  const date = new Date(d)
  const day = date.getDay()
  const diff = day === 0 ? -6 : 1 - day
  date.setDate(date.getDate() + diff)
  date.setHours(0, 0, 0, 0)
  return date
}

export function toISODate(d) {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

export function formatWeekLabel(mondayIso) {
  const start = new Date(mondayIso + 'T00:00:00')
  const end = new Date(start)
  end.setDate(end.getDate() + 5)
  const fmt = (x) =>
    x.toLocaleDateString('fr-FR', { day: '2-digit', month: 'short' })
  return `${fmt(start)} — ${fmt(end)}`
}

export function todayNameFr() {
  const names = ['Dimanche', 'Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi']
  return names[new Date().getDay()]
}

export function formatTime(t) {
  if (!t) return ''
  return String(t).slice(0, 5)
}
