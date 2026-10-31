"use client";
import { useQuery } from "@tanstack/react-query";
import { BellRing, CalendarClock, ShieldCheck } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { health } from "@/lib/api";
import ThemeToggle from "@/components/ThemeToggle";
import { useAuth } from "@/lib/auth";

const DEMO: [string, string][] = [
  ["inst.kaveri@demo.test", "Institution"], ["inst.northfield@demo.test", "Institution"],
  ["scrutiny1@demo.test", "Scrutiny"], ["scrutiny2@demo.test", "Scrutiny"],
  ["regional.south@demo.test", "Regional"], ["regional.north@demo.test", "Regional"],
  ["bureau.gc@demo.test", "Bureau"], ["bureau.rb@demo.test", "Bureau"], ["admin@demo.test", "Admin"],
];
const DEMO_MODE = process.env.NEXT_PUBLIC_DEMO_MODE !== "false";
const POINTS = [
  [CalendarClock, "One obligation engine", "Expiries, SLAs and visits tracked on a single calendar."],
  [BellRing, "Escalation you can see", "Every alert step is logged and explainable."],
  [ShieldCheck, "Advisory, audited", "The system flags. People decide. Every action is hash-chained."],
] as const;

export default function Login() {
  const { login, t, user } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const api = useQuery({ queryKey: ["health"], queryFn: health });

  useEffect(() => {
    if (user) router.replace("/");
  }, [user, router]);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setErr("");
    setBusy(true);
    try {
      await login(email, password);
      router.replace("/");
    } catch (x) {
      setErr((x as Error).message);
      setBusy(false);
    }
  }
  const online = api.data?.status === "ok";
  const input = "mt-1 min-h-11 w-full rounded-lg border border-border bg-surface px-3 py-2";

  return (
    <div className="grid min-h-screen lg:grid-cols-[1.1fr_1fr]">
      <aside className="hidden flex-col justify-between bg-[var(--nav-bg)] p-12 text-white lg:flex">
        <div className="flex items-center gap-3">
          <span className="grid size-11 place-items-center rounded-xl bg-white/10 text-xl font-bold">W</span>
          <span className="text-2xl font-bold">{t("app.name")}</span>
        </div>
        <div>
          <h2 className="max-w-md text-4xl font-bold leading-tight">
            Every deadline, approval and complaint in one place.
          </h2>
          <ul className="mt-8 grid max-w-md gap-5">
            {POINTS.map(([Icon, h, p]) => (
              <li key={h} className="flex gap-3">
                <span className="grid size-10 shrink-0 place-items-center rounded-lg bg-white/10"><Icon size={20} aria-hidden /></span>
                <div><div className="font-bold">{h}</div><div className="text-[color:var(--nav-text)]">{p}</div></div>
              </li>
            ))}
          </ul>
        </div>
        <p className="text-sm text-[color:var(--nav-text)]">{t("footer")}</p>
      </aside>

      <main className="relative flex items-center justify-center p-6">
        <div className="absolute right-4 top-4"><ThemeToggle /></div>
        <div className="w-full max-w-md">
          <h1 className="text-3xl font-bold lg:hidden">{t("app.name")}</h1>
          <h2 className="mt-2 text-2xl font-bold lg:mt-0">{t("login.title")}</h2>
          <p className="mb-5 flex items-center gap-2 text-sm text-text-2" aria-live="polite">
            <span className={`size-2.5 rounded-full ${api.isLoading ? "bg-[var(--muted)]" : online ? "bg-[var(--fulfilled)]" : "bg-[var(--overdue)]"}`} />
            API {api.isLoading ? "checking…" : online ? "online" : "unreachable"}
          </p>
          <form onSubmit={submit} className="card space-y-4 p-5">
            <label className="block font-bold">
              {t("login.email")}
              <input type="email" required autoComplete="username" value={email}
                onChange={(e) => setEmail(e.target.value)} className={`${input} font-normal`} />
            </label>
            <label className="block font-bold">
              {t("login.password")}
              <input type="password" required autoComplete="current-password" value={password}
                onChange={(e) => setPassword(e.target.value)} className={`${input} font-normal`} />
            </label>
            {err && <p role="alert" className="font-bold text-overdue">{err}</p>}
            <button disabled={busy} className="min-h-11 w-full rounded-lg bg-primary px-3 py-2 font-bold text-white disabled:opacity-60">
              {busy ? "Signing in…" : t("login.submit")}
            </button>
          </form>
          {DEMO_MODE && (
            <section className="mt-6">
              <h3 className="mb-2 text-sm font-bold text-text-2">{t("login.demo")}</h3>
              <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
                {DEMO.map(([d, role]) => (
                  <button key={d} type="button" onClick={() => { setEmail(d); setPassword("Demo@1234"); }}
                    className="card min-h-11 px-3 py-2 text-left hover:border-primary">
                    <div className="text-xs text-text-2">{role}</div>
                    <div className="truncate text-sm font-bold">{d.split("@")[0]}</div>
                  </button>
                ))}
              </div>
            </section>
          )}
          <p className="mt-8 text-xs text-text-2 lg:hidden">{t("footer")}</p>
        </div>
      </main>
    </div>
  );
}
