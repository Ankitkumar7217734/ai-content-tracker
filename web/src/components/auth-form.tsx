"use client";

import { createClient } from "@/lib/supabase/client";
import { GoogleSignInButton } from "@/components/google-sign-in-button";
import { useState } from "react";

type Tab = "signin" | "signup";

export function AuthForm() {
  const [tab, setTab] = useState<Tab>("signin");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleEmailAuth(event: React.FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    setMessage(null);

    const supabase = createClient();

    try {
      if (tab === "signup") {
        const { data, error: signUpError } = await supabase.auth.signUp({
          email,
          password,
          options: {
            data: { display_name: displayName || undefined },
            emailRedirectTo: `${window.location.origin}/auth/callback`,
          },
        });

        if (signUpError) throw signUpError;

        if (data.session) {
          window.location.assign("/dashboard");
          return;
        }

        setMessage(
          "Account created. Check your email to confirm, then sign in.",
        );
        setTab("signin");
        return;
      }

      const { data, error: signInError } = await supabase.auth.signInWithPassword(
        {
          email,
          password,
        },
      );

      if (signInError) throw signInError;

      if (data.session) {
        window.location.assign("/dashboard");
        return;
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Authentication failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex rounded-xl border border-[var(--card-border)] p-1">
        <button
          type="button"
          onClick={() => {
            setTab("signin");
            setError(null);
            setMessage(null);
          }}
          className={`flex-1 rounded-lg py-2 text-sm font-medium transition ${
            tab === "signin"
              ? "bg-[var(--accent)] text-white"
              : "text-[var(--muted)] hover:text-white"
          }`}
        >
          Sign in
        </button>
        <button
          type="button"
          onClick={() => {
            setTab("signup");
            setError(null);
            setMessage(null);
          }}
          className={`flex-1 rounded-lg py-2 text-sm font-medium transition ${
            tab === "signup"
              ? "bg-[var(--accent)] text-white"
              : "text-[var(--muted)] hover:text-white"
          }`}
        >
          Create account
        </button>
      </div>

      <form onSubmit={handleEmailAuth} className="space-y-4">
        {tab === "signup" && (
          <div>
            <label className="label" htmlFor="displayName">
              Display name
            </label>
            <input
              id="displayName"
              className="input"
              placeholder="Your name"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
            />
          </div>
        )}

        <div>
          <label className="label" htmlFor="email">
            Email
          </label>
          <input
            id="email"
            type="email"
            className="input"
            required
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>

        <div>
          <label className="label" htmlFor="password">
            Password
          </label>
          <input
            id="password"
            type="password"
            className="input"
            required
            minLength={6}
            autoComplete={
              tab === "signup" ? "new-password" : "current-password"
            }
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>

        {message && (
          <p className="text-sm text-[var(--success)]">{message}</p>
        )}
        {error && <p className="text-sm text-[var(--danger)]">{error}</p>}

        <button type="submit" className="btn-primary w-full" disabled={loading}>
          {loading
            ? "Please wait…"
            : tab === "signup"
              ? "Create account"
              : "Sign in with email"}
        </button>
      </form>

      <div className="relative">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-[var(--card-border)]" />
        </div>
        <div className="relative flex justify-center text-xs uppercase">
          <span className="bg-[var(--card)] px-2 text-[var(--muted)]">or</span>
        </div>
      </div>

      <GoogleSignInButton />
    </div>
  );
}
