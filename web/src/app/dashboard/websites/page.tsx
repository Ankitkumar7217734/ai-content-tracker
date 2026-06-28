"use client";

import { createClient } from "@/lib/supabase/client";
import { useEffect, useState } from "react";

type TrackedUrl = {
  id: string;
  site_name: string;
  url: string;
  last_checked_at: string | null;
};

export default function TrackWebsitesPage() {
  const [urls, setUrls] = useState<TrackedUrl[]>([]);
  const [siteName, setSiteName] = useState("");
  const [url, setUrl] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [userId, setUserId] = useState<string | null>(null);

  async function loadUrls(uid: string) {
    const supabase = createClient();
    const { data } = await supabase
      .from("tracked_urls")
      .select("*")
      .eq("user_id", uid)
      .order("created_at", { ascending: false });
    setUrls(data ?? []);
  }

  useEffect(() => {
    async function init() {
      const supabase = createClient();
      const {
        data: { user },
      } = await supabase.auth.getUser();
      if (user) {
        setUserId(user.id);
        await loadUrls(user.id);
      }
    }
    init();
  }, []);

  async function handleAdd(event: React.FormEvent) {
    event.preventDefault();
    if (!userId) return;
    setError(null);

    const supabase = createClient();
    const { error: insertError } = await supabase.from("tracked_urls").insert({
      user_id: userId,
      site_name: siteName || url,
      url,
      url_type: "website",
    });

    if (insertError) {
      setError(insertError.message);
      return;
    }

    setSiteName("");
    setUrl("");
    await loadUrls(userId);
  }

  async function handleDelete(id: string) {
    if (!userId) return;
    const supabase = createClient();
    await supabase.from("tracked_urls").delete().eq("id", id);
    await loadUrls(userId);
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Track Websites</h1>
        <p className="mt-1 text-sm text-[var(--muted)]">
          Checked weekly. Examples: OpenAI News, Anthropic Research.
        </p>
      </div>

      <form onSubmit={handleAdd} className="card space-y-4 p-6">
        <div>
          <label className="label" htmlFor="siteName">
            Site name
          </label>
          <input
            id="siteName"
            className="input"
            placeholder="OpenAI News"
            value={siteName}
            onChange={(e) => setSiteName(e.target.value)}
          />
        </div>
        <div>
          <label className="label" htmlFor="url">
            URL
          </label>
          <input
            id="url"
            className="input"
            required
            placeholder="https://openai.com/news/"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
          />
        </div>
        {error && <p className="text-sm text-[var(--danger)]">{error}</p>}
        <button type="submit" className="btn-primary">
          Add URL
        </button>
      </form>

      <div className="card divide-y divide-[var(--card-border)]">
        {urls.length === 0 ? (
          <p className="p-6 text-sm text-[var(--muted)]">No URLs yet.</p>
        ) : (
          urls.map((row) => (
            <div key={row.id} className="flex items-center justify-between gap-4 p-4">
              <div>
                <p className="font-medium">{row.site_name}</p>
                <p className="text-sm text-[var(--muted)]">
                  {row.url} (last checked: {row.last_checked_at ?? "never"})
                </p>
              </div>
              <button
                type="button"
                onClick={() => handleDelete(row.id)}
                className="btn-secondary text-sm text-[var(--danger)]"
              >
                Delete
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
