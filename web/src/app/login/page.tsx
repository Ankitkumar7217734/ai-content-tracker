"use client";

import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { AuthForm } from "@/components/auth-form";

function AuthErrorBanner() {
  const searchParams = useSearchParams();
  const error = searchParams.get("error");
  const description = searchParams.get("error_description");

  if (!error) return null;

  let message =
    "Sign-in failed. Please try again or use email/password below.";

  if (description?.includes("invalid_client") || description?.includes("Unable to exchange external code")) {
    message =
      "Google rejected Supabase’s credentials: the Client Secret (or Client ID) in Supabase → Authentication → Providers → Google is wrong. Reset the secret in Google Cloud Console, paste both values again in Supabase, and Save.";
  } else if (description?.includes("OAuth state parameter missing") || description?.includes("state parameter")) {
    message =
      "OAuth session expired or was interrupted. Clear site cookies for localhost, close extra tabs, then click Continue with Google once in a fresh private window.";
  } else if (description) {
    message = description;
  } else if (error === "auth") {
    message = "Authentication was cancelled or incomplete.";
  }

  return (
    <div className="mb-6 rounded-xl border border-[var(--danger)]/30 bg-[var(--danger)]/10 px-4 py-3 text-sm text-red-200">
      {message}
    </div>
  );
}

export default function LoginPage() {
  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <div className="card w-full max-w-md p-8">
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-[var(--accent)]/15 text-2xl">
            📡
          </div>
          <h1 className="text-2xl font-bold">AI Content Tracker</h1>
          <p className="mt-2 text-sm text-[var(--muted)]">
            Create an account or sign in to generate reports and track YouTube
            channels &amp; websites.
          </p>
        </div>

        <Suspense fallback={null}>
          <AuthErrorBanner />
        </Suspense>

        <AuthForm />

        <p className="mt-6 text-center text-xs text-[var(--muted)]">
          Each account gets a stable user ID. Scheduled jobs email the address
          in Settings.
        </p>
      </div>
    </div>
  );
}
