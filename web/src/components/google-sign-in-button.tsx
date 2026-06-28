"use client";

import { createClient } from "@/lib/supabase/client";
import { useState } from "react";

const GOOGLE_ENABLED =
  process.env.NEXT_PUBLIC_GOOGLE_AUTH_ENABLED === "true";

const SUPABASE_PROJECT = "vkulsgzcwhvnsputwapm";
const GOOGLE_CALLBACK = `https://${SUPABASE_PROJECT}.supabase.co/auth/v1/callback`;

export function GoogleSignInButton() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showSetup, setShowSetup] = useState(!GOOGLE_ENABLED);

  async function signInWithGoogle() {
    if (!GOOGLE_ENABLED) {
      setShowSetup(true);
      return;
    }

    setLoading(true);
    setError(null);
    const supabase = createClient();
    const { error: authError } = await supabase.auth.signInWithOAuth({
      provider: "google",
      options: {
        redirectTo: `${window.location.origin}/auth/callback`,
      },
    });
    if (authError) {
      const msg = authError.message.includes("provider is not enabled")
        ? "Google is still not enabled in Supabase. Complete the setup steps below, then set NEXT_PUBLIC_GOOGLE_AUTH_ENABLED=true in web/.env.local and restart the app."
        : authError.message;
      setError(msg);
      setShowSetup(true);
      setLoading(false);
    }
  }

  return (
    <div className="space-y-3">
      <button
        type="button"
        onClick={signInWithGoogle}
        disabled={loading}
        className="flex w-full items-center justify-center gap-3 rounded-xl border border-[var(--card-border)] bg-white px-4 py-3 font-medium text-gray-900 transition hover:bg-gray-100 disabled:opacity-60"
      >
        <svg viewBox="0 0 24 24" className="h-5 w-5" aria-hidden="true">
          <path
            fill="#4285F4"
            d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
          />
          <path
            fill="#34A853"
            d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
          />
          <path
            fill="#FBBC05"
            d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
          />
          <path
            fill="#EA4335"
            d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
          />
        </svg>
        {loading ? "Redirecting…" : "Continue with Google"}
      </button>

      {error && <p className="text-sm text-[var(--danger)]">{error}</p>}

      {(showSetup || !GOOGLE_ENABLED) && (
        <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-4 text-sm">
          <p className="font-medium text-amber-200">
            Google sign-in requires one-time Supabase setup
          </p>
          <p className="mt-2 text-[var(--muted)]">
            Google is enabled, but Supabase auth logs show{" "}
            <strong>invalid_client: The provided client secret is invalid</strong>.
            Re-copy the Client Secret from Google Cloud and paste it in Supabase.
            Email/password above works without this.
          </p>
          <ol className="mt-3 list-decimal space-y-2 pl-5 text-[var(--muted)]">
            <li>
              Google Cloud → create OAuth client → add redirect URI:
              <code className="mt-1 block break-all rounded bg-black/30 px-2 py-1 text-xs text-white">
                {GOOGLE_CALLBACK}
              </code>
            </li>
            <li>
              <a
                href={`https://supabase.com/dashboard/project/${SUPABASE_PROJECT}/auth/providers`}
                target="_blank"
                rel="noreferrer"
                className="text-[var(--accent)] underline"
              >
                Supabase → Authentication → Providers → Google
              </a>
              {" "}→ Enable → paste Client ID + Secret → Save
            </li>
            <li>
              <a
                href={`https://supabase.com/dashboard/project/${SUPABASE_PROJECT}/auth/url-configuration`}
                target="_blank"
                rel="noreferrer"
                className="text-[var(--accent)] underline"
              >
                Supabase → URL Configuration
              </a>
              {" "}→ add redirect URL:
              <code className="mt-1 block rounded bg-black/30 px-2 py-1 text-xs text-white">
                http://localhost:3000/auth/callback
              </code>
            </li>
            <li>
              In <code className="text-white">web/.env.local</code> set{" "}
              <code className="text-white">NEXT_PUBLIC_GOOGLE_AUTH_ENABLED=true</code>{" "}
              and restart the web app
            </li>
          </ol>
          <button
            type="button"
            onClick={() => setShowSetup(false)}
            className="mt-3 text-xs text-[var(--muted)] underline"
          >
            Hide setup steps
          </button>
        </div>
      )}
    </div>
  );
}
