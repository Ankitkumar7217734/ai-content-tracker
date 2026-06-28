"use client";

import { createClient } from "@/lib/supabase/client";
import { apiFetch } from "@/lib/api";
import { useEffect, useState } from "react";

type Channel = {
  id: string;
  channel_id: string;
  channel_url: string;
  channel_name: string | null;
};

export default function TrackYouTubePage() {
  const [channels, setChannels] = useState<Channel[]>([]);
  const [channelUrl, setChannelUrl] = useState("");
  const [channelName, setChannelName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [userId, setUserId] = useState<string | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(null);

  async function loadChannels(uid: string) {
    const supabase = createClient();
    const { data } = await supabase
      .from("youtube_channels")
      .select("*")
      .eq("user_id", uid)
      .order("created_at", { ascending: false });
    setChannels(data ?? []);
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
        await loadChannels(user.id);
      }
    }
    init();
  }, []);

  async function handleAdd(event: React.FormEvent) {
    event.preventDefault();
    if (!userId || !accessToken) return;
    setError(null);

    let channelId: string;
    try {
      const resolved = await apiFetch<{ channel_id: string }>(
        "/youtube/resolve-channel",
        accessToken,
        {
          method: "POST",
          body: JSON.stringify({ channel_url: channelUrl }),
        },
      );
      channelId = resolved.channel_id;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not resolve channel");
      return;
    }

    const supabase = createClient();
    const { error: insertError } = await supabase.from("youtube_channels").insert({
      user_id: userId,
      channel_id: channelId,
      channel_url: channelUrl,
      channel_name: channelName || channelId,
    });

    if (insertError) {
      setError(insertError.message);
      return;
    }

    setChannelUrl("");
    setChannelName("");
    await loadChannels(userId);
  }

  async function handleDelete(id: string) {
    if (!userId) return;
    const supabase = createClient();
    await supabase.from("youtube_channels").delete().eq("id", id);
    await loadChannels(userId);
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Track YouTube Channels</h1>
        <p className="mt-1 text-sm text-[var(--muted)]">
          Checked every 24 hours. New videos trigger a report emailed to your
          notification address.
        </p>
      </div>

      <form onSubmit={handleAdd} className="card space-y-4 p-6">
        <div>
          <label className="label" htmlFor="channelUrl">
            Channel URL
          </label>
          <input
            id="channelUrl"
            className="input"
            required
            placeholder="https://www.youtube.com/@krishnaik06"
            value={channelUrl}
            onChange={(e) => setChannelUrl(e.target.value)}
          />
        </div>
        <div>
          <label className="label" htmlFor="channelName">
            Label (optional)
          </label>
          <input
            id="channelName"
            className="input"
            placeholder="Krish Naik"
            value={channelName}
            onChange={(e) => setChannelName(e.target.value)}
          />
        </div>
        {error && <p className="text-sm text-[var(--danger)]">{error}</p>}
        <button type="submit" className="btn-primary">
          Add channel
        </button>
      </form>

      <div className="card divide-y divide-[var(--card-border)]">
        {channels.length === 0 ? (
          <p className="p-6 text-sm text-[var(--muted)]">No channels yet.</p>
        ) : (
          channels.map((ch) => (
            <div key={ch.id} className="flex items-center justify-between gap-4 p-4">
              <div>
                <p className="font-medium">{ch.channel_name ?? ch.channel_id}</p>
                <p className="text-sm text-[var(--muted)]">{ch.channel_url}</p>
              </div>
              <button
                type="button"
                onClick={() => handleDelete(ch.id)}
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
