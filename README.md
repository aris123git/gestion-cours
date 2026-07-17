# GestionCours — Hybrid Timetable System

Windows **desktop app for administrators** + **student web portal**, synchronized through a FastAPI backend backed by **Supabase**.

```
┌─────────────────────┐         POST /sync          ┌──────────────────┐
│  Desktop (Tkinter)  │ ──────────────────────────► │  FastAPI         │
│  SQLite local DB    │   X-API-Key                 │  + Supabase      │
│  + desktop_sync/    │                             └────────┬─────────┘
└─────────────────────┘                                      │
                                                             │ GET /schedule
                                                             ▼
                                                    ┌──────────────────┐
                                                    │ React student    │
                                                    │ portal (PWA)     │
                                                    └──────────────────┘
```

## Features

### Admin desktop (existing + sync)
- Full timetable editing (filières, rooms, allocation, PDF export)
- **Sync button** + status bar
- **Automatic sync** after every save / reset / tronc commun
- **Conflict detection** when the server is newer
- **Offline queue** with automatic retry when connectivity returns

### Student website
- Landing page, login (student number + bcrypt password)
- Dashboard: name, programme, level, current week, today’s courses, weekly grid
- Filters: week / programme / level + search
- Color-coded course cards (subject, teacher, room, time, group)
- Dark mode, notifications on timetable changes
- Print / PDF download, responsive mobile-first layout, PWA offline cache

## Project layout

```
supabase/          SQL schema + setup notes (hosted Postgres)
backend/           FastAPI + supabase-py (service role)
frontend/          React + Vite + Tailwind (student PWA)
desktop_sync/      Sync client used by the Tkinter app
docs/API.md        REST documentation
scripts/           Student creation helper
docker-compose.yml API + frontend (no local Postgres)
*.py               Existing Windows desktop application
```

## Supabase setup (required)

1. Create a project at [supabase.com](https://supabase.com).
2. Run [`supabase/migrations/20260717000000_initial_schema.sql`](supabase/migrations/20260717000000_initial_schema.sql) in the SQL Editor.
3. Copy Project URL + **service_role** key into `backend/.env` (see [`supabase/README.md`](supabase/README.md)).

```bash
cp backend/.env.example backend/.env
# edit SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY
cd backend && pip install -r requirements.txt && python -m app.seed
```

## Quick start (Docker)

```bash
# Export Supabase credentials first
export SUPABASE_URL=https://xxxx.supabase.co
export SUPABASE_SERVICE_ROLE_KEY=eyJ...
docker compose up --build
```

- API docs: http://localhost:8000/docs  
- Student portal: http://localhost:3000  
- Demo login: `20250001` / `password123`

## Local development

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # set Supabase keys
uvicorn app.main:app --reload --port 8000
python -m app.seed
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 (Vite proxies `/api` → `:8000`).

### Desktop admin

```bash
pip install -r requirements.txt
export GESTION_API_URL=http://127.0.0.1:8000
export GESTION_API_KEY=desktop-admin-sync-key-change-me
python main.py
```

Use **☁ Synchroniser** or save a course — changes are pushed to Supabase via the API.

## Environment variables

| Variable | Component | Purpose |
|----------|-----------|---------|
| `SUPABASE_URL` | backend | Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | backend | Server key (never expose to browsers) |
| `SUPABASE_ANON_KEY` | optional | Public anon key if SPA talks to Supabase later |
| `SECRET_KEY` | backend | JWT signing |
| `ADMIN_API_KEY` | backend / desktop | Desktop sync key (`X-API-Key`) |
| `CORS_ORIGINS` | backend | Allowed frontends |
| `GESTION_API_URL` | desktop | API base URL |
| `GESTION_API_KEY` | desktop | Same as `ADMIN_API_KEY` |
| `VITE_API_URL` | frontend | API base (use `/api` behind nginx) |

## Database tables (Supabase)

`students`, `filieres`, `teachers`, `rooms`, `courses`, `schedule`, `notifications`  
Schema: `supabase/migrations/20260717000000_initial_schema.sql`.

Local desktop SQLite (`gestion_cours.db`) remains the admin working copy and syncs online.

## Synchronization flow

1. Admin saves locally (SQLite).
2. Desktop calls `POST /sync` with filières, rooms, and schedules (`desktop_id` for idempotency).
3. API upserts / deletes in Supabase; notifies students of the affected filière.
4. Student portal polls notifications and refreshes the schedule.

If the network is down, changes are stored in `sync_queue.json` and flushed automatically when `/health` responds again.

## Creating students

```bash
cd backend && python ../scripts/create_student.py \
  --number 20250003 --first Jean --last Dupont \
  --email jean@univ.example --filiere-id 1 --level L1 \
  --password secret123
```

## License

Internal university project — adapt as needed.
