"use client";

import { createClient } from "@/lib/supabase/client";
import { apiFetch } from "@/lib/api";
import { useEffect, useState } from "react";

export default function SettingsPage() {
  const [userId, setUserId] = useState<string | null>(null);
  const [userEmail, setUserEmail] = useState<string | null>(null);
  const [notificationEmail, setNotificationEmail] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [allowScheduled, setAllowScheduled] = useState(true);
  const [hasKey, setHasKey] = useState(false);
  const [schedulingOn, setSchedulingOn] = useState(false);
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function loadProfile(uid: string) {
    const supabase = createClient();
    const { data: profile } = await supabase
      .from("profiles")
      .select("*")
      .eq("user_id", uid)
      .single();

    if (profile) {
      setNotificationEmail(profile.notification_email ?? "");
      setDisplayName(profile.display_name ?? "");
    }

    const { data: secrets } = await supabase
      .from("user_secrets")
      .select("*")
      .eq("user_id", uid)
      .maybeSingle();

    setHasKey(Boolean(secrets?.openai_api_key_encrypted));
    setSchedulingOn(Boolean(secrets?.allow_scheduled_jobs));
    setAllowScheduled(secrets?.allow_scheduled_jobs ?? true);
  }

  useEffect(() => {
    async function init() {
      const supabase = createClient();
      const {
        data: { user },
      } = await supabase.auth.getUser();
      const {
        data: { session },
      } = await supabase.auth.getSession();
      setAccessToken(session?.access_token ?? null);
      if (user) {
        setUserId(user.id);
        setUserEmail(user.email ?? null);
        await loadProfile(user.id);
      }
    }
    init();
  }, []);

  async function saveProfile(event: React.FormEvent) {
    event.preventDefault();
    if (!userId) return;
    setMessage(null);
    setError(null);

    const supabase = createClient();
    const { error: updateError } = await supabase
      .from("profiles")
      .update({ notification_email: notificationEmail, display_name: displayName })
      .eq("user_id", userId);

    if (updateError) {
      setError(updateError.message);
      return;
    }
    setMessage("Profile saved. Scheduled emails will go to this address.");
  }

  async function saveApiKey(event: React.FormEvent) {
    event.preventDefault();
    if (!accessToken) return;
    setMessage(null);
    setError(null);

    try {
      await apiFetch("/settings/api-key", accessToken, {
        method: "POST",
        body: JSON.stringify({
          openai_api_key: apiKey,
          allow_scheduled_jobs: allowScheduled,
        }),
      });
      setApiKey("");
      setHasKey(true);
      setSchedulingOn(allowScheduled);
      setMessage("API key saved securely.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save key");
    }
  }

  async function removeApiKey() {
    if (!accessToken) return;
    setMessage(null);
    setError(null);

    try {
      await apiFetch("/settings/api-key", accessToken, { method: "DELETE" });
      setHasKey(false);
      setSchedulingOn(false);
      setMessage("API key removed.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not remove key");
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Settings</h1>
        <p className="mt-1 text-sm text-[var(--muted)]">
          Your Google account maps to a stable user ID used by scheduled jobs.
        </p>
      </div>

      <div className="card p-6">
        <h2 className="font-semibold">Account</h2>
        <dl className="mt-3 space-y-2 text-sm">
          <div>
            <dt className="text-[var(--muted)]">Google email</dt>
            <dd>{userEmail}</dd>
          </div>
          <div>
            <dt className="text-[var(--muted)]">User ID (used by schedulers)</dt>
            <dd className="font-mono text-xs break-all">{userId}</dd>
          </div>
        </dl>
      </div>

      {message && (
        <div className="rounded-lg border border-[var(--success)]/30 bg-[var(--success)]/10 px-4 py-3 text-sm">
          {message}
        </div>
      )}
      {error && (
        <div className="rounded-lg border border-[var(--danger)]/30 bg-[var(--danger)]/10 px-4 py-3 text-sm">
          {error}
        </div>
      )}

      <form onSubmit={saveProfile} className="card space-y-4 p-6">
        <h2 className="font-semibold">Profile</h2>
        <div>
          <label className="label" htmlFor="notificationEmail">
            Notification email (receives scheduled reports)
          </label>
          <input
            id="notificationEmail"
            type="email"
            className="input"
            value={notificationEmail}
            onChange={(e) => setNotificationEmail(e.target.value)}
          />
        </div>
        <div>
          <label className="label" htmlFor="displayName">
            Display name
          </label>
          <input
            id="displayName"
            className="input"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
          />
        </div>
        <button type="submit" className="btn-primary">
          Save profile
        </button>
      </form>

      <div className="card space-y-4 p-6">
        <h2 className="font-semibold">OpenAI API key (for automation)</h2>
        <p className="text-sm text-[var(--muted)]">
          Encrypted server-side. Used by daily YouTube and weekly website jobs to
          generate reports and email you.
        </p>

        {hasKey && (
          <div className="rounded-lg bg-black/20 px-4 py-3 text-sm">
            API key saved.
            {schedulingOn ? " Scheduled reports enabled." : " Scheduled reports disabled."}
            <button
              type="button"
              onClick={removeApiKey}
              className="ml-3 text-[var(--danger)] underline"
            >
              Remove
            </button>
          </div>
        )}

        <form onSubmit={saveApiKey} className="space-y-4">
          <div>
            <label className="label" htmlFor="openaiKey">
              OpenAI API key
            </label>
            <input
              id="openaiKey"
              type="password"
              className="input"
              placeholder="sk-..."
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
            />
          </div>
          <label className="flex items-center gap-2 text-sm text-[var(--muted)]">
            <input
              type="checkbox"
              checked={allowScheduled}
              onChange={(e) => setAllowScheduled(e.target.checked)}
            />
            Enable automatic scheduled reports
          </label>
          <button type="submit" className="btn-primary" disabled={!apiKey.trim()}>
            Save API key
          </button>
        </form>
      </div>
    </div>
  );
}
