# Supabase setup

GestionCours stores the online timetable in **Supabase** (hosted PostgreSQL + REST).

## 1. Create a project

1. Open [https://supabase.com](https://supabase.com) and create a project.
2. Copy **Project URL**, **anon** key, and **service_role** key from **Project Settings → API**.

## 2. Apply the schema

In the Supabase **SQL Editor**, run:

[`migrations/20260717000000_initial_schema.sql`](migrations/20260717000000_initial_schema.sql)

Or with the Supabase CLI:

```bash
supabase link --project-ref <your-ref>
supabase db push
```

## 3. Configure the backend

```bash
cp backend/.env.example backend/.env
```

Set:

```env
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOi...   # service_role — never expose to the browser
SECRET_KEY=...
ADMIN_API_KEY=...
```

## 4. Seed demo data

```bash
cd backend
pip install -r requirements.txt
python -m app.seed
```

Demo students: `20250001` / `password123` and `20250002` / `password123`.

## Notes

- The FastAPI backend uses the **service role** key and keeps JWT login for students.
- Desktop SQLite stays local; `desktop_sync/` still pushes to `POST /sync`.
- Do not put the service role key in the React app.
