"use client";

import { createClient } from "@/lib/supabase/client";
import { apiPdfUrl } from "@/lib/api";
import { useEffect, useState } from "react";

type Report = {
  id: string;
  topic: string | null;
  source_url: string | null;
  source_type: string;
  markdown: string;
  created_at: string;
};

export default function ReportHistoryPage() {
  const [reports, setReports] = useState<Report[]>([]);
  const [accessToken, setAccessToken] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      const supabase = createClient();
      const {
        data: { session },
      } = await supabase.auth.getSession();
      setAccessToken(session?.access_token ?? null);

      if (!session?.user) return;
      const { data } = await supabase
        .from("reports")
        .select("*")
        .eq("user_id", session.user.id)
        .order("created_at", { ascending: false })
        .limit(50);
      setReports(data ?? []);
    }
    load();
  }, []);

  function downloadMarkdown(report: Report) {
    const blob = new Blob([report.markdown], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${report.topic ?? "report"}.md`;
    link.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Report History</h1>
        <p className="mt-1 text-sm text-[var(--muted)]">Your last 50 generated reports.</p>
      </div>

      {reports.length === 0 ? (
        <div className="card p-6 text-sm text-[var(--muted)]">No reports yet.</div>
      ) : (
        <div className="space-y-4">
          {reports.map((report) => (
            <details key={report.id} className="card p-4">
              <summary className="cursor-pointer font-medium">
                {report.topic ?? "Report"} — {report.created_at.slice(0, 10)}
              </summary>
              <p className="mt-2 text-sm text-[var(--muted)]">
                Source: {report.source_url ?? "N/A"} ({report.source_type})
              </p>
              <div className="mt-3 flex gap-3">
                <button
                  type="button"
                  onClick={() => downloadMarkdown(report)}
                  className="btn-secondary text-sm"
                >
                  Download .md
                </button>
                {accessToken && (
                  <button
                    type="button"
                    className="btn-secondary text-sm"
                    onClick={() => {
                      fetch(apiPdfUrl(report.id), {
                        headers: { Authorization: `Bearer ${accessToken}` },
                      })
                        .then((r) => r.blob())
                        .then((blob) => {
                          const url = URL.createObjectURL(blob);
                          const link = document.createElement("a");
                          link.href = url;
                          link.download = `${report.topic ?? "report"}.pdf`;
                          link.click();
                          URL.revokeObjectURL(url);
                        });
                    }}
                  >
                    Download .pdf
                  </button>
                )}
              </div>
              <div className="prose-report mt-4 rounded-lg bg-black/20 p-4">
                {report.markdown}
              </div>
            </details>
          ))}
        </div>
      )}
    </div>
  );
}
