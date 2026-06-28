import Link from "next/link";
import { createClient } from "@/lib/supabase/server";
import { SignOutButton } from "@/components/sign-out-button";

const navItems = [
  { href: "/dashboard", label: "Generate Report" },
  { href: "/dashboard/youtube", label: "Track YouTube" },
  { href: "/dashboard/websites", label: "Track Websites" },
  { href: "/dashboard/history", label: "Report History" },
  { href: "/dashboard/settings", label: "Settings" },
];

export async function DashboardShell({
  children,
}: {
  children: React.ReactNode;
}) {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  const profile = user
    ? (
        await supabase
          .from("profiles")
          .select("display_name, notification_email")
          .eq("user_id", user.id)
          .single()
      ).data
    : null;

  return (
    <div className="min-h-screen">
      <header className="border-b border-[var(--card-border)] bg-[var(--card)]/80 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <div>
            <Link href="/dashboard" className="text-lg font-semibold">
              AI Content Tracker
            </Link>
            <p className="text-sm text-[var(--muted)]">
              {profile?.display_name ?? user?.email}
            </p>
          </div>
          <SignOutButton />
        </div>
      </header>

      <div className="mx-auto grid max-w-6xl gap-8 px-6 py-8 lg:grid-cols-[220px_1fr]">
        <nav className="card h-fit p-3">
          <ul className="space-y-1">
            {navItems.map((item) => (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className="block rounded-lg px-3 py-2 text-sm text-[var(--muted)] transition hover:bg-white/5 hover:text-white"
                >
                  {item.label}
                </Link>
              </li>
            ))}
          </ul>
          <div className="mt-4 border-t border-[var(--card-border)] pt-4 text-xs text-[var(--muted)]">
            <p className="font-mono break-all">User ID</p>
            <p className="mt-1 font-mono text-[10px] leading-relaxed text-white/70">
              {user?.id}
            </p>
            <p className="mt-3">Emails go to</p>
            <p className="mt-1 text-white/80">
              {profile?.notification_email ?? user?.email}
            </p>
          </div>
        </nav>

        <main>{children}</main>
      </div>
    </div>
  );
}
