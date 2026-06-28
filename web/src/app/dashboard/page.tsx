"use client";

import { createClient } from "@/lib/supabase/client";
import { apiFetch, apiPdfUrl } from "@/lib/api";
import { useEffect, useState } from "react";

type ReportResult = {
  id: string;
  topic: string;
  markdown: string;
  filename: string;
};

export default function GenerateReportPage() {
  const [sourceType, setSourceType] = useState<"youtube" | "website">("youtube");
  const [sourceUrl, setSourceUrl] = useState("");
  const [topic, setTopic] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [saveKey, setSaveKey] = useState(false);
  const [hasSavedKey, setHasSavedKey] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<ReportResult | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(null);

  useEffect(() => {
    async function loadSession() {
      const supabase = createClient();
      const {
        data: { session },
      } = await supabase.auth.getSession();
      setAccessToken(session?.access_token ?? null);

      if (session?.user) {
        const { data } = await supabase
          .from("user_secrets")
          .select("openai_api_key_encrypted")
          .eq("user_id", session.user.id)
          .maybeSingle();
        setHasSavedKey(Boolean(data?.openai_api_key_encrypted));
      }
    }
    loadSession();
  }, []);

  async function handleGenerate(event: React.FormEvent) {
    event.preventDefault();
    if (!accessToken) return;

    setLoading(true);
    setError(null);
    setReport(null);

    try {
      const result = await apiFetch<ReportResult>("/reports/generate", accessToken, {
        method: "POST",
        body: JSON.stringify({
          source_type: sourceType,
          source_url: sourceUrl,
          topic,
          openai_api_key: apiKey || undefined,
          save_api_key: saveKey && Boolean(apiKey),
        }),
      });
      setReport(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Generation failed");
    } finally {
      setLoading(false);
    }
  }

  function downloadMarkdown() {
    if (!report) return;
    const blob = new Blob([report.markdown], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = report.filename;
    link.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Generate Report</h1>
        <p className="mt-1 text-sm text-[var(--muted)]">
          Paste a YouTube or website URL. Uses your saved API key or a one-time key.
        </p>
      </div>

      {hasSavedKey && (
        <div className="rounded-lg border border-[var(--success)]/30 bg-[var(--success)]/10 px-4 py-3 text-sm">
          Saved OpenAI API key found in Settings.
        </div>
      )}

      <form onSubmit={handleGenerate} className="card space-y-4 p-6">
        <div>
          <label className="label" htmlFor="apiKey">
            OpenAI API Key {hasSavedKey ? "(optional if saved)" : "(required)"}
          </label>
          <input
            id="apiKey"
            type="password"
            className="input"
            placeholder="sk-..."
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
          />
          {apiKey && (
            <label className="mt-2 flex items-center gap-2 text-sm text-[var(--muted)]">
              <input
                type="checkbox"
                checked={saveKey}
                onChange={(e) => setSaveKey(e.target.checked)}
              />
              Save this key for scheduled reports
            </label>
          )}
        </div>

        <div className="flex gap-4">
          {(["youtube", "website"] as const).map((type) => (
            <label key={type} className="flex items-center gap-2 text-sm">
              <input
                type="radio"
                name="sourceType"
                checked={sourceType === type}
                onChange={() => setSourceType(type)}
              />
              {type === "youtube" ? "YouTube video" : "Website URL"}
            </label>
          ))}
        </div>

        <div>
          <label className="label" htmlFor="sourceUrl">
            {sourceType === "youtube" ? "YouTube Video URL" : "Website URL"}
          </label>
          <input
            id="sourceUrl"
            className="input"
            required
            placeholder={
              sourceType === "youtube"
                ? "https://www.youtube.com/watch?v=..."
                : "https://openai.com/news/..."
            }
            value={sourceUrl}
            onChange={(e) => setSourceUrl(e.target.value)}
          />
        </div>

        <div>
          <label className="label" htmlFor="topic">
            Topic
          </label>
          <input
            id="topic"
            className="input"
            required
            placeholder="e.g. AI vs ML vs Data Science"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
          />
        </div>

        {error && <p className="text-sm text-[var(--danger)]">{error}</p>}

        <button type="submit" className="btn-primary" disabled={loading}>
          {loading ? "Running CrewAI agents… (1–2 min)" : "Generate Report"}
        </button>
      </form>

      {report && (
        <div className="card space-y-4 p-6">
          <div className="flex flex-wrap gap-3">
            <button type="button" onClick={downloadMarkdown} className="btn-secondary">
              Download Markdown
            </button>
            {accessToken && (
              <a
                href={`${apiPdfUrl(report.id)}`}
                className="btn-secondary"
                onClick={(e) => {
                  e.preventDefault();
                  fetch(apiPdfUrl(report.id), {
                    headers: { Authorization: `Bearer ${accessToken}` },
                  })
                    .then((r) => r.blob())
                    .then((blob) => {
                      const url = URL.createObjectURL(blob);
                      const link = document.createElement("a");
                      link.href = url;
                      link.download = report.filename.replace(".md", ".pdf");
                      link.click();
                      URL.revokeObjectURL(url);
                    });
                }}
              >
                Download PDF
              </a>
            )}
          </div>
          <div className="prose-report rounded-lg bg-black/20 p-4">{report.markdown}</div>
        </div>
      )}
    </div>
  );
}
