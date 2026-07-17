# API Documentation — GestionCours

Interactive OpenAPI docs are available at **`/docs`** (Swagger UI) and **`/redoc`** when the backend is running.

Base URL (local): `http://127.0.0.1:8000`

Data store: **Supabase** (PostgreSQL). The FastAPI layer uses the service role key.

## Authentication

### Student JWT

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/login` | — | Login with `student_number` + `password`. Returns JWT + profile. |
| GET | `/student` | Bearer | Current student profile. |

**Login body:**

```json
{
  "student_number": "20250001",
  "password": "password123"
}
```

**Header for student routes:** `Authorization: Bearer <access_token>`

Passwords are hashed with **bcrypt** (`passlib`).

### Admin API key (desktop sync)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/sync` | `X-API-Key` | Full timetable sync from desktop. |
| POST | `/admin/sync` | `X-API-Key` | Same as `/sync`. |
| PUT | `/schedule` | `X-API-Key` | Upsert one schedule entry. |
| DELETE | `/schedule/{id}` | `X-API-Key` | Delete schedule by server id. |
| PATCH | `/admin/schedule/{id}` | `X-API-Key` | Partial update. |

Default API key (change in production): `desktop-admin-sync-key-change-me`

## Student endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/schedule` | Week schedule. Query: `week`, `filiere_id`, `level`, `search`. |
| GET | `/schedule/week/{date}` | Schedule for the week containing `date`. |
| GET | `/filieres` | List programmes. Query: `level`. |
| GET | `/notifications` | Student notifications. Query: `unread_only`. |
| POST | `/notifications/{id}/read` | Mark notification as read. |

## Sync payload (`POST /sync`)

```json
{
  "filieres": [{ "desktop_id": 1, "name": "Informatique", "level": "L1" }],
  "rooms": [{ "desktop_id": 1, "name": "A101", "capacity": 40 }],
  "schedules": [{
    "desktop_id": 42,
    "filiere_desktop_id": 1,
    "day": "Lundi",
    "start_time": "07:00:00",
    "end_time": "12:00:00",
    "subject": "Algorithmique",
    "teacher": "Dr. Dupont",
    "room": "Labo Info",
    "group_tc": null,
    "week_date": "2026-07-13"
  }],
  "deleted_desktop_ids": [99],
  "notify_students": true
}
```

Schedules are matched by `desktop_id` to **never create duplicates**.  
If the server copy is newer than the client `updated_at`, a **conflict** is reported and the client row is skipped.

## Health

`GET /health` → `{ "status": "ok", "version": "2.0.0" }`
