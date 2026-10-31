"use client";
import { useQuery } from "@tanstack/react-query";
import { AlertTriangle, CalendarClock, CalendarDays, ChevronLeft, ChevronRight, ListChecks, Timer } from "lucide-react";
import { useState } from "react";
import {
  Bar, BarChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import { EmptyState, ErrorState, KpiTile, PageHeader, Skeleton, STATUS_ORDER, StatusChip, statusColor, statusLabel } from "@/components/ui";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";

type Dash = {
  total: number; open: number; by_status: Record<string, number>;
  by_type: Record<string, Record<string, number>>; upcoming: Record<string, number>;
  top_overdue: { institution_id: string; name: string; overdue: number }[];
};
type Cal = { days: Record<string, { id: string; title: string; type: string; status: string }[]> };
const pretty = (s: string) => s.replace(/_/g, " ").toLowerCase().replace(/^\w/, (c) => c.toUpperCase());
const axis = { fontSize: 12, fill: "var(--text-2)" };
const tip = { background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 8, color: "var(--text)" };

function CalendarGrid() {
  const [m, setM] = useState(() => new Date().toISOString().slice(0, 7));
  const [pick, setPick] = useState<string | null>(null);
  const q = useQuery({ queryKey: ["calendar", m], queryFn: () => api<Cal>(`/obligations/calendar?month=${m}`) });
  const [y, mo] = m.split("-").map(Number);
  const first = new Date(Date.UTC(y, mo - 1, 1)).getUTCDay();
  const len = new Date(Date.UTC(y, mo, 0)).getUTCDate();
  const shift = (d: number) => setM(new Date(Date.UTC(y, mo - 1 + d, 1)).toISOString().slice(0, 7));
  const key = (d: number) => `${m}-${String(d).padStart(2, "0")}`;
  const list = pick ? q.data?.days[pick] ?? [] : [];
  return (
    <div className="card p-4">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="font-bold">{new Date(Date.UTC(y, mo - 1, 1)).toLocaleDateString("en-IN", { month: "long", year: "numeric", timeZone: "UTC" })}</h2>
        <div className="flex gap-1">
          <button aria-label="Previous month" className="grid size-11 place-items-center rounded-lg border border-border" onClick={() => shift(-1)}><ChevronLeft size={18} /></button>
          <button aria-label="Next month" className="grid size-11 place-items-center rounded-lg border border-border" onClick={() => shift(1)}><ChevronRight size={18} /></button>
        </div>
      </div>
      <div className="grid grid-cols-7 gap-1 text-center text-xs font-bold text-text-2">
        {["S", "M", "T", "W", "T", "F", "S"].map((d, i) => <div key={i}>{d}</div>)}
      </div>
      <div className="mt-1 grid grid-cols-7 gap-1">
        {Array.from({ length: first }, (_, i) => <div key={`b${i}`} />)}
        {Array.from({ length: len }, (_, i) => {
          const items = q.data?.days[key(i + 1)] ?? [];
          const worst = items.find((x) => x.status === "OVERDUE") ?? items[0];
          return (
            <button key={i} onClick={() => setPick(key(i + 1))} aria-label={`${i + 1}, ${items.length} due`}
              className={`flex min-h-11 flex-col items-center justify-center rounded-lg border text-sm ${pick === key(i + 1) ? "border-primary bg-primary-soft" : "border-transparent hover:bg-surface-2"}`}>
              {i + 1}
              {worst && <span className="mt-0.5 size-2 rounded-full" style={{ background: statusColor(worst.status) }} />}
            </button>
          );
        })}
      </div>
      {pick && (
        <ul className="mt-3 grid gap-1 border-t border-border pt-3">
          {list.length === 0 && <li className="text-text-2">Nothing due on {pick}.</li>}
          {list.map((o) => (
            <li key={o.id} className="flex items-center justify-between gap-2"><span>{o.title}</span><StatusChip status={o.status} /></li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default function Compliance() {
  const { t } = useAuth();
  const [view, setView] = useState<"charts" | "calendar">("charts");
  const q = useQuery({ queryKey: ["compliance"], queryFn: () => api<Dash>("/dashboards/compliance") });
  const d = q.data;
  const types = d ? Object.entries(d.by_type).map(([type, c]) => ({ type: pretty(type), ...c })) : [];
  const donut = d ? STATUS_ORDER.filter((s) => d.by_status[s]).map((s) => ({ name: statusLabel(s), key: s, value: d.by_status[s] })) : [];
  const up = d ? [{ w: "≤ 30 days", n: d.upcoming["30"] }, { w: "31–60 days", n: d.upcoming["60"] }, { w: "61–90 days", n: d.upcoming["90"] }] : [];
  const toggle = (v: typeof view, label: string, Icon: typeof CalendarDays) => (
    <button aria-pressed={view === v} onClick={() => setView(v)}
      className={`inline-flex min-h-11 items-center gap-2 px-4 font-bold ${view === v ? "bg-primary text-white" : "text-text-2"}`}>
      <Icon size={16} aria-hidden /> {label}
    </button>
  );

  return (
    <>
      <PageHeader title={t("nav.compliance")} subtitle="Obligations across documents, undertakings, FDRs and SLAs"
        actions={<div className="flex overflow-hidden rounded-lg border border-border">{toggle("charts", "Overview", ListChecks)}{toggle("calendar", "Calendar", CalendarDays)}</div>} />
      {q.isLoading && <Skeleton />}
      {q.error && <ErrorState message={t("state.error")} onRetry={() => q.refetch()} retryLabel={t("state.retry")} />}
      {d && d.total === 0 && <EmptyState title={t("state.empty")} hint="Obligations appear here once created." />}
      {d && d.total > 0 && view === "calendar" && <CalendarGrid />}
      {d && d.total > 0 && view === "charts" && (
        <div className="grid gap-5">
          <div className="grid grid-cols-2 gap-4 xl:grid-cols-4">
            <KpiTile label="Open obligations" value={d.open} icon={ListChecks} />
            <KpiTile label="Overdue" value={d.by_status.OVERDUE ?? 0} icon={AlertTriangle} tone="var(--overdue)" hint="needs action" />
            <KpiTile label="Due within 30 days" value={d.upcoming["30"]} icon={Timer} tone="var(--due-soon)" />
            <KpiTile label="Due in 31–90 days" value={d.upcoming["60"] + d.upcoming["90"]} icon={CalendarClock} tone="var(--upcoming)" />
          </div>

          <div className="grid gap-5 lg:grid-cols-[1fr_1.4fr]">
            <section className="card p-4" aria-label="Status mix">
              <h2 className="font-bold">Status mix</h2>
              <div className="relative h-56">
                <ResponsiveContainer>
                  <PieChart>
                    <Pie data={donut} dataKey="value" nameKey="name" innerRadius={62} outerRadius={90} paddingAngle={2} stroke="none">
                      {donut.map((s) => <Cell key={s.key} fill={statusColor(s.key)} />)}
                    </Pie>
                    <Tooltip contentStyle={tip} />
                  </PieChart>
                </ResponsiveContainer>
                <div className="pointer-events-none absolute inset-0 grid place-items-center text-center">
                  <div><div className="text-3xl font-bold tabular-nums">{d.total}</div><div className="text-xs text-text-2">total</div></div>
                </div>
              </div>
              <ul className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-sm">
                {donut.map((s) => (
                  <li key={s.key} className="flex items-center gap-1.5">
                    <span className="size-2.5 rounded-sm" style={{ background: statusColor(s.key) }} /> {s.name} <b>{s.value}</b>
                  </li>
                ))}
              </ul>
            </section>

            <section className="card p-4" aria-label="By type">
              <h2 className="font-bold">By obligation type</h2>
              <div className="h-64">
                <ResponsiveContainer>
                  <BarChart data={types} layout="vertical" margin={{ left: 20 }}>
                    <CartesianGrid horizontal={false} stroke="var(--border)" />
                    <XAxis type="number" allowDecimals={false} tick={axis} />
                    <YAxis type="category" dataKey="type" width={120} tick={axis} />
                    <Tooltip contentStyle={tip} cursor={{ fill: "var(--surface-2)" }} />
                    {STATUS_ORDER.map((s) => <Bar key={s} name={statusLabel(s)} dataKey={s} stackId="a" fill={statusColor(s)} />)}
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </section>
          </div>

          <div className="grid gap-5 lg:grid-cols-2">
            <section className="card p-4" aria-label="Upcoming">
              <h2 className="font-bold">Coming up</h2>
              <ul className="mt-3 grid gap-3">
                {up.map((u) => {
                  const max = Math.max(1, ...up.map((x) => x.n));
                  return (
                    <li key={u.w}>
                      <div className="flex justify-between text-sm"><span>{u.w}</span><b className="tabular-nums">{u.n}</b></div>
                      <div className="mt-1 h-2.5 rounded-full bg-surface-2">
                        <div className="h-full rounded-full bg-[var(--upcoming)]" style={{ width: `${(u.n / max) * 100}%` }} />
                      </div>
                    </li>
                  );
                })}
              </ul>
            </section>

            <section className="card p-4" aria-label="Top overdue">
              <h2 className="font-bold">Institutions with most overdue</h2>
              {d.top_overdue.length === 0 && <p className="mt-3 text-text-2">Nothing overdue.</p>}
              <ol className="mt-3 grid gap-2">
                {d.top_overdue.map((o, i) => (
                  <li key={o.institution_id} className="flex items-center gap-3">
                    <span className="grid size-7 place-items-center rounded-full bg-[var(--overdue-bg)] text-sm font-bold text-overdue">{i + 1}</span>
                    <span className="flex-1">{o.name}</span>
                    <StatusChip status="OVERDUE" /> <b className="tabular-nums">{o.overdue}</b>
                  </li>
                ))}
              </ol>
            </section>
          </div>
        </div>
      )}
    </>
  );
}
