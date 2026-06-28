# AI Content Tracker

Custom web app (Next.js) with Google sign-in, Supabase database, CrewAI report generation, and scheduled monitoring for YouTube channels and websites.

> **Legacy:** The Streamlit UI in `app/streamlit_app.py` still works but is no longer the primary interface.

## How it works

| Flow | Trigger | What happens |
|------|---------|----------------|
| **Manual report** | User pastes a video or website URL | CrewAI generates a report; user downloads md/pdf |
| **YouTube tracking** | GitHub Actions every 24h | RSS finds new videos → report → email |
| **Website tracking** | GitHub Actions weekly | Scraper finds new links → report → email |

Each Google-authenticated user gets a stable **Supabase user ID** (`auth.users.id`). Scheduled jobs look up that ID, read `profiles.notification_email`, and send reports there.

Scheduled jobs use **each user's own encrypted OpenAI API key** — no app-owner LLM billing.

## Setup

### 1. Supabase

1. Create a project at https://supabase.com/dashboard
2. Run [`sql/schema.sql`](sql/schema.sql) in the SQL Editor  
   (If you already ran an older schema, also run [`sql/migration_user_secrets.sql`](sql/migration_user_secrets.sql))
3. Run [`sql/migration_google_oauth.sql`](sql/migration_google_oauth.sql) for Google profile metadata
4. Copy keys to `.env` (see [`.env.example`](.env.example))

### 2. Google OAuth (Supabase)

1. Create OAuth credentials at https://console.cloud.google.com/apis/credentials
2. Authorized redirect URI: `https://<your-project-ref>.supabase.co/auth/v1/callback`
3. Supabase Dashboard → **Authentication → Providers → Google** → enable and paste Client ID + Secret
4. Supabase Dashboard → **Authentication → URL Configuration** → add redirect URLs:
   - `http://localhost:3000/auth/callback` (local dev)
   - `https://your-domain.com/auth/callback` (production)

### 3. Encryption key

Generate once and add to `.env` and GitHub secrets:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 4. Local environment

```bash
python3.11 -m venv venv2
source venv2/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your keys

cd web && cp .env.local.example .env.local && cd ..
# Edit web/.env.local (same SUPABASE_URL + ANON_KEY)
npm install --prefix web
```

### 5. Run the web app

Terminal 1 — Python API (report generation + encrypted API keys):

```bash
source venv2/bin/activate
uvicorn api.main:app --reload --port 8000
```

Terminal 2 — Next.js frontend:

```bash
cd web && npm run dev
```

Open http://localhost:3000 and sign in with Google.

### 6. User onboarding

Each user must:

1. Sign in with Google
2. Confirm **notification email** in Settings (defaults to Google email)
3. Save their **OpenAI API key** in Settings (encrypted) and enable scheduled reports
4. Add YouTube channels or website URLs to track

After that, reports are generated and emailed automatically — no need to visit the app.

### 7. GitHub Actions (scheduled jobs)

Add these secrets in your GitHub repo → Settings → Secrets:

| Secret | Purpose |
|--------|---------|
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_ANON_KEY` | Anon public key |
| `SUPABASE_SERVICE_ROLE_KEY` | Service role (workers only) |
| `ENCRYPTION_KEY` | Decrypt per-user API keys |
| `RESEND_API_KEY` | Email API key |
| `RESEND_FROM_EMAIL` | Verified sender email |

- **Daily (24h):** `.github/workflows/daily_youtube.yml` — YouTube RSS check
- **Weekly:** `.github/workflows/weekly_urls.yml` — website URL check

Jobs resolve users by `user_id` on tracked rows → `profiles.notification_email`. No changes needed for the new web UI.

### 8. Legacy Streamlit (optional)

```bash
streamlit run app/streamlit_app.py
```

## Project structure

```
web/           Next.js frontend (Google OAuth, Tailwind UI)
api/           FastAPI backend (CrewAI, encrypted API keys, PDF)
app/           Legacy Streamlit UI, encryption, PDF helpers
crew/          CrewAI factory (video + website crews)
jobs/          Scheduled checkers + email
sql/           Supabase schema + migrations
.github/       GitHub Actions workflows
```

## Security

- User OpenAI keys are **encrypted at rest** (`user_secrets` table + `ENCRYPTION_KEY`)
- `SUPABASE_SERVICE_ROLE_KEY` is for GitHub Actions workers only
- Enable RLS policies from `schema.sql`
- Do **not** set an app-level `OPENAI_API_KEY` — each user brings their own
