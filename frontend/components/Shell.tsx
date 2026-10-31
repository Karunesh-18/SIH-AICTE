"use client";
import { useQuery } from "@tanstack/react-query";
import {
  AlertOctagon, BarChart3, Bell, CalendarDays, ClipboardCheck, Cog, FileText, Gauge, GitCompare,
  History, Home, Inbox, LayoutDashboard, ListTodo, LogOut, Menu, MessageSquareWarning, Play,
  Building2, ShieldAlert, Users, X, type LucideIcon,
} from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { NAV } from "@/lib/nav";
import ThemeToggle from "./ThemeToggle";

const ICON: Record<string, LucideIcon> = {
  home: Home, applications: ClipboardCheck, documents: FileText, obligations: ListTodo,
  complaints: MessageSquareWarning, notifications: Bell, "work-queue": Inbox, pendency: Gauge,
  compliance: BarChart3, evc: CalendarDays, institutions: Building2, risk: ShieldAlert,
  "complaint-queue": Inbox, overlaps: GitCompare, "complaint-dashboard": LayoutDashboard,
  config: Cog, users: Users, audit: History, demo: Play,
};
const ROLE: Record<string, string> = {
  INSTITUTION: "Institution", SCRUTINY_OFFICER: "Scrutiny officer", REGIONAL_OFFICER: "Regional officer",
  BUREAU_OFFICER: "Bureau officer", ADMIN: "Admin",
};

export default function Shell({ children }: { children: React.ReactNode }) {
  const { user, ready, t, lang, setLang, logout } = useAuth();
  const router = useRouter();
  const path = usePathname();
  const [open, setOpen] = useState(false);
  const unread = useQuery({
    queryKey: ["notifications"], enabled: !!user, refetchInterval: 30_000,
    queryFn: () => api<{ unread_count: number }>("/notifications?unread=true"),
  });

  useEffect(() => {
    if (ready && !user) router.replace("/login");
  }, [ready, user, router]);

  if (!ready || !user) return <p className="p-6 text-text-2">{t("state.loading")}</p>;

  const count = unread.data?.unread_count ?? 0;
  const slugs = NAV[user.role].filter((s) => s !== "notifications");
  const current = t(`nav.${path.split("/")[1]}`);

  const nav = (
    <ul className="space-y-0.5">
      {slugs.map((slug) => {
        const href = `/${slug}`;
        const active = path === href || path.startsWith(`${href}/`);
        const Icon = ICON[slug] ?? AlertOctagon;
        return (
          <li key={slug}>
            <Link
              href={href}
              onClick={() => setOpen(false)}
              aria-current={active ? "page" : undefined}
              className={`flex min-h-11 items-center gap-3 rounded-lg px-3 py-2 font-bold ${
                active ? "bg-[var(--nav-active-bg)] text-[color:var(--nav-active)]" : "text-[color:var(--nav-text)] hover:bg-white/5 hover:text-white"
              }`}
            >
              <Icon size={19} aria-hidden /> {t(`nav.${slug}`)}
            </Link>
          </li>
        );
      })}
    </ul>
  );

  return (
    <div className="flex min-h-screen flex-col">
      <a href="#main" className="sr-only focus:not-sr-only focus:absolute focus:z-50 focus:bg-surface focus:p-3">
        Skip to content
      </a>
      <div className="flex flex-1">
        <aside
          className={`${open ? "fixed inset-0 z-40 block w-64" : "hidden"} shrink-0 flex-col bg-[var(--nav-bg)] p-3 md:sticky md:top-0 md:flex md:h-screen md:w-64`}
        >
          <div className="mb-5 flex items-center gap-2 px-2 pt-1">
            <span className="grid size-9 place-items-center rounded-lg bg-white/10 text-lg font-bold text-white">W</span>
            <div className="leading-tight text-white">
              <div className="text-lg font-bold">{t("app.name")}</div>
              <div className="text-xs text-[color:var(--nav-text)]">Compliance &amp; approvals</div>
            </div>
            <button className="ml-auto text-white md:hidden" aria-label="Close menu" onClick={() => setOpen(false)}>
              <X />
            </button>
          </div>
          <nav aria-label="Main" className="flex-1 overflow-y-auto">{nav}</nav>
          <div className="mt-3 rounded-lg bg-white/5 p-3 text-xs text-[color:var(--nav-text)]">
            <div className="font-bold text-white">{user.full_name}</div>
            {ROLE[user.role]}
          </div>
        </aside>

        <div className="flex min-w-0 flex-1 flex-col">
          <header className="sticky top-0 z-30 flex items-center gap-2 border-b border-border bg-surface/95 px-4 py-2 backdrop-blur">
            <button className="grid size-11 place-items-center rounded-lg border border-border md:hidden"
              aria-label="Menu" aria-expanded={open} onClick={() => setOpen(true)}>
              <Menu size={20} />
            </button>
            <span className="font-bold text-text-2">{current}</span>
            <div className="ml-auto flex items-center gap-2">
              <div role="group" aria-label="Language" className="flex overflow-hidden rounded-lg border border-border">
                {(["en", "hi"] as const).map((l) => (
                  <button key={l} aria-pressed={lang === l} onClick={() => setLang(l)}
                    className={`min-h-11 px-3 font-bold ${lang === l ? "bg-primary text-white" : "text-text-2"}`}>
                    {l === "en" ? "EN" : "हिंदी"}
                  </button>
                ))}
              </div>
              <ThemeToggle />
              <Link href="/notifications" aria-label={`${t("nav.notifications")}${count ? `, ${count} unread` : ""}`}
                className="relative grid size-11 place-items-center rounded-lg border border-border">
                <Bell size={20} aria-hidden />
                {count > 0 && (
                  <span className="absolute -right-1.5 -top-1.5 grid min-w-5 place-items-center rounded-full bg-[var(--overdue)] px-1 text-xs font-bold text-white">
                    {count > 99 ? "99+" : count}
                  </span>
                )}
              </Link>
              <button className="inline-flex min-h-11 items-center gap-2 rounded-lg border border-border px-3 font-bold"
                onClick={() => { logout(); router.replace("/login"); }}>
                <LogOut size={17} aria-hidden /> <span className="hidden sm:inline">{t("logout")}</span>
              </button>
            </div>
          </header>
          <main id="main" className="min-w-0 flex-1 p-4 md:p-8">{children}</main>
          <footer className="border-t border-border bg-surface px-4 py-3 text-xs text-text-2">
            {t("footer")}
          </footer>
        </div>
      </div>
    </div>
  );
}
