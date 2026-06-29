# Deployment (Render)

Everything runs on [Render](https://render.com): Next.js frontend + FastAPI backend. Supabase handles auth and the database.

## Live stack

| Service | Render name | Purpose |
|---------|-------------|---------|
| **Frontend** | `ai-content-tracker-web` | Next.js app in `web/` |
| **API** | `ai-content-tracker-api` | FastAPI + CrewAI in `api/` |
| **Database / Auth** | Supabase | Already hosted |

## 1. Push to GitHub

Ensure the repo is on GitHub (e.g. `Ankitkumar7217734/ai-content-tracker`).

## 2. Deploy with Blueprint

1. Open [Render Dashboard](https://dashboard.render.com) → **New** → **Blueprint**
2. Connect your GitHub repo
3. Render reads `render.yaml` and creates **two** web services
4. When prompted, set these secrets (same values as your local `.env`):

   | Variable | Used by |
   |----------|---------|
   | `SUPABASE_URL` | API + frontend |
   | `SUPABASE_ANON_KEY` | API + frontend |
   | `ENCRYPTION_KEY` | API only |
   | `NEXT_PUBLIC_SUPABASE_URL` | Frontend (same as `SUPABASE_URL`) |
   | `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Frontend (same as `SUPABASE_ANON_KEY`) |

5. Click **Apply** and wait for both services to build

`NEXT_PUBLIC_API_URL` and `ALLOWED_ORIGINS` are wired automatically between the two services via `render.yaml`.

## 3. Note your URLs

After deploy:

- **Frontend:** `https://ai-content-tracker-web.onrender.com` (or your custom name)
- **API:** `https://ai-content-tracker-api.onrender.com`

Test the API: `https://ai-content-tracker-api.onrender.com/health` → `{"status":"ok"}`

## 4. Supabase URL configuration

In Supabase → **Authentication** → **URL Configuration**:

- **Site URL:** your Render frontend URL, e.g. `https://ai-content-tracker-web.onrender.com`
- **Redirect URLs** (add both):
  - `https://ai-content-tracker-web.onrender.com/auth/callback`
  - `http://localhost:3000/auth/callback` (local dev)

## 5. Google OAuth (optional)

If using Google sign-in:

1. Google Cloud Console → OAuth client → authorized redirect URI stays:
   `https://<your-project>.supabase.co/auth/v1/callback`
2. Supabase → Auth → Providers → Google → paste Client ID + Secret
3. `NEXT_PUBLIC_GOOGLE_AUTH_ENABLED=true` is already set in `render.yaml`

## 6. GitHub Actions (scheduled jobs)

Add repo secrets for YouTube/website cron jobs (see root `README.md`):

- `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `RESEND_API_KEY`, etc.

## Free tier notes

- **Cold starts:** Free web services sleep after ~15 min of inactivity. First request may take 30–60 seconds.
- **API builds:** Installing CrewAI on Render can take several minutes on the first deploy.
- **Timeouts:** Report generation can take 1–2 minutes; if you hit timeouts on the free plan, upgrade the API service or split long jobs to a background worker.

## Local development

```bash
# Terminal 1 — API
venv2/bin/uvicorn api.main:app --reload --port 8000

# Terminal 2 — frontend
cd web && npm run dev
```

Set `web/.env.local` from `web/.env.local.example` with `NEXT_PUBLIC_API_URL=http://localhost:8000`.
