# Enable Google Sign-In (Supabase)

## Error: `Unable to exchange external code: 4/0A`

This means Google login **started correctly** but Supabase could not finish it. Your Supabase auth logs show:

**`invalid_client: The provided client secret is invalid`**

The `4/0A` is just part of the OAuth code — ignore it. Fix the **Client Secret** (and verify Client ID) in Supabase.

### Fix (5 minutes)

1. **Google Cloud Console** → https://console.cloud.google.com/apis/credentials  
2. Open your **Web application** OAuth client (not Android/iOS)  
3. Click **Reset secret** → copy the **new** Client Secret immediately  
4. Also copy the **Client ID** from the same page  
5. **Supabase** → https://supabase.com/dashboard/project/vkulsgzcwhvnsputwapm/auth/providers → **Google**  
6. Paste **Client ID** in Client ID field  
7. Paste **Client Secret** in Client Secret field (no spaces before/after)  
8. Click **Save**  
9. Try Google sign-in again at http://localhost:3000/login  

### Checklist

| Check | Required value |
|-------|----------------|
| OAuth client type | **Web application** |
| Google redirect URI | `https://vkulsgzcwhvnsputwapm.supabase.co/auth/v1/callback` |
| Supabase redirect URL | `http://localhost:3000/auth/callback` |
| Client ID in Supabase | Same as Google Cloud (ends in `.apps.googleusercontent.com`) |
| Client Secret in Supabase | Same as Google Cloud (starts with `GOCSPX-`) |

---

## Full setup (first time)

The error `Unsupported provider: provider is not enabled` means Google OAuth is **not turned on** in your Supabase project yet. Email/password works without this setup.

## Step 1 — Google Cloud OAuth credentials

1. Open https://console.cloud.google.com/apis/credentials
2. Create a project (or pick an existing one)
3. **APIs & Services → OAuth consent screen** → configure (External is fine for testing)
4. **Credentials → Create credentials → OAuth client ID**
   - Application type: **Web application**
   - Authorized redirect URI (required):

     ```
     https://vkulsgzcwhvnsputwapm.supabase.co/auth/v1/callback
     ```

5. Copy the **Client ID** and **Client Secret**

## Step 2 — Enable Google in Supabase

1. Open https://supabase.com/dashboard/project/vkulsgzcwhvnsputwapm/auth/providers
2. Find **Google** → toggle **Enable**
3. Paste Client ID and Client Secret → **Save**

## Step 3 — Redirect URLs for local dev

1. Open https://supabase.com/dashboard/project/vkulsgzcwhvnsputwapm/auth/url-configuration
2. Under **Redirect URLs**, add:

   ```
   http://localhost:3000/auth/callback
   ```

3. Save

## Step 4 — Test

1. Restart the web app if it is running
2. Go to http://localhost:3000/login
3. Click **Continue with Google**

## Both sign-in methods

| Method | Status |
|--------|--------|
| Email + password (Create account / Sign in tabs) | Works now — no extra setup |
| Google OAuth | Requires Steps 1–3 above |

Both methods create the same Supabase `user_id` and `profiles` row, so scheduled emails work the same way.
