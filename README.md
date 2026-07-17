# GestionCours — Hybrid Timetable System

Windows **desktop app for administrators** + **student web portal**, synchronized through a FastAPI backend.

```
┌─────────────────────┐         POST /sync          ┌──────────────────┐
│  Desktop (Tkinter)  │ ──────────────────────────► │  FastAPI + PG    │
│  SQLite local DB    │   X-API-Key                 │  JWT for students│
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
backend/           FastAPI + SQLAlchemy + Alembic
frontend/          React + Vite + Tailwind (student PWA)
desktop_sync/      Sync client used by the Tkinter app
docs/API.md        REST documentation
scripts/           Student creation helper
docker-compose.yml PostgreSQL + API + frontend
*.py               Existing Windows desktop application
```

## Quick start (Docker)

```bash
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
cp .env.example .env
# For a quick local demo without Postgres:
# export DATABASE_URL=sqlite:///./gestion_online.db
uvicorn app.main:app --reload --port 8000
python -m app.seed
```

Migrations (PostgreSQL):

```bash
cd backend
alembic upgrade head
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
# Point sync at the API:
export GESTION_API_URL=http://127.0.0.1:8000
export GESTION_API_KEY=desktop-admin-sync-key-change-me
python main.py
```

Use **☁ Synchroniser** or save a course — changes are pushed to the online database.

## Environment variables

| Variable | Component | Purpose |
|----------|-----------|---------|
| `DATABASE_URL` | backend | SQLAlchemy URL |
| `SECRET_KEY` | backend | JWT signing |
| `ADMIN_API_KEY` | backend / desktop | Desktop sync key (`X-API-Key`) |
| `CORS_ORIGINS` | backend | Allowed frontends |
| `GESTION_API_URL` | desktop | API base URL |
| `GESTION_API_KEY` | desktop | Same as `ADMIN_API_KEY` |
| `VITE_API_URL` | frontend | API base (use `/api` behind nginx) |

## Database tables

`students`, `filieres`, `teachers`, `rooms`, `courses`, `schedule`, `notifications`  
See Alembic migration `backend/alembic/versions/001_initial_schema.py`.

## Synchronization flow

1. Admin saves locally (SQLite).
2. Desktop calls `POST /sync` with filières, rooms, and schedules (`desktop_id` for idempotency).
3. Server upserts / deletes; notifies students of the affected filière.
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
