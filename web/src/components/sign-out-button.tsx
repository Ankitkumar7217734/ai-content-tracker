"use client";

import { createClient } from "@/lib/supabase/client";

export function SignOutButton() {
  async function handleSignOut() {
    const supabase = createClient();
    await supabase.auth.signOut();
    window.location.assign("/login");
  }

  return (
    <button type="button" onClick={handleSignOut} className="btn-secondary text-sm">
      Sign out
    </button>
  );
}
