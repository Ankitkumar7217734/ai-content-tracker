# Deployment

## GitHub

This repo contains only the **AI Content Tracker** app (`web/`, `api/`, `app/`, `crew/`, `jobs/`, `sql/`).

Excluded folders (course projects) are listed in `.gitignore`.

## Live stack

| Service | Host | Purpose |
|---------|------|---------|
| **Frontend** | [Vercel](https://vercel.com) | Next.js app in `web/` |
| **API** | [Render](https://render.com) | FastAPI in `api/` |
| **Database / Auth** | [Supabase](https://supabase.com) | Already hosted |

## 1. Deploy API (Render)

1. Push this repo to GitHub
2. [Render Dashboard](https://dashboard.render.com) → **New** → **Blueprint**
3. Connect the repo → Render reads `render.yaml`
4. Set secret env vars when prompted:
   - `SUPABASE_URL`
   - `SUPABASE_ANON_KEY`
   - `ENCRYPTION_KEY`
   - `ALLOWED_ORIGINS` = your Vercel URL, e.g. `https://your-app.vercel.app`
5. Note the API URL, e.g. `https://ai-content-tracker-api.onrender.com`

## 2. Deploy frontend (Vercel)

1. [Vercel Dashboard](https://vercel.com/new) → Import GitHub repo
2. Set **Root Directory** to `web`
3. Add environment variables:
   - `NEXT_PUBLIC_SUPABASE_URL`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`
   - `NEXT_PUBLIC_API_URL` = Render API URL from step 1
   - `NEXT_PUBLIC_GOOGLE_AUTH_ENABLED` = `true`
4. Deploy

## 3. Supabase URL configuration

In Supabase → Authentication → URL Configuration:

- **Site URL**: `https://your-app.vercel.app`
- **Redirect URLs**:
  - `https://your-app.vercel.app/auth/callback`
  - `http://localhost:3000/auth/callback` (local dev)

## 4. GitHub Actions (scheduled jobs)

Add the same secrets already documented in README to GitHub repo secrets for YouTube/website cron jobs.
