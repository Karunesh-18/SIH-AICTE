"use client";
import {
  AlertTriangle, CheckCircle2, CircleDashed, Clock, Inbox, MinusCircle, PauseCircle, RotateCw,
  type LucideIcon,
} from "lucide-react";

/** Status = colour + icon + text (docs/05 principle 2). */
const STATUS: Record<string, { label: string; icon: LucideIcon; fg: string; bg: string }> = {
  UPCOMING: { label: "Upcoming", icon: CircleDashed, fg: "var(--upcoming)", bg: "var(--upcoming-bg)" },
  DUE_SOON: { label: "Due soon", icon: Clock, fg: "var(--due-soon)", bg: "var(--due-soon-bg)" },
  OVERDUE: { label: "Overdue", icon: AlertTriangle, fg: "var(--overdue)", bg: "var(--overdue-bg)" },
  FULFILLED: { label: "Fulfilled", icon: CheckCircle2, fg: "var(--fulfilled)", bg: "var(--fulfilled-bg)" },
  WAIVED: { label: "Waived", icon: MinusCircle, fg: "var(--muted)", bg: "var(--muted-bg)" },
  PAUSED: { label: "Paused", icon: PauseCircle, fg: "var(--muted)", bg: "var(--muted-bg)" },
};
export const STATUS_ORDER = Object.keys(STATUS);
export const statusColor = (s: string) => STATUS[s]?.fg ?? "var(--muted)";
export const statusLabel = (s: string) => STATUS[s]?.label ?? s;

export function StatusChip({ status }: { status: string }) {
  const s = STATUS[status] ?? STATUS.PAUSED;
  const Icon = s.icon;
  return (
    <span
      className="inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-bold"
      style={{ color: s.fg, background: s.bg }}
    >
      <Icon size={13} aria-hidden /> {STATUS[status] ? s.label : status}
    </span>
  );
}

export function PageHeader({ title, subtitle, actions }: {
  title: string; subtitle?: string; actions?: React.ReactNode;
}) {
  return (
    <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">{title}</h1>
        {subtitle && <p className="text-text-2">{subtitle}</p>}
      </div>
      {actions}
    </div>
  );
}

export function KpiTile({ label, value, icon: Icon, tone = "var(--primary)", hint }: {
  label: string; value: number | string; icon: LucideIcon; tone?: string; hint?: string;
}) {
  return (
    <div className="card rise flex items-center gap-3 p-4">
      <span
        className="grid size-11 shrink-0 place-items-center rounded-xl"
        style={{ color: tone, background: `color-mix(in srgb, ${tone} 14%, transparent)` }}
      >
        <Icon size={22} aria-hidden />
      </span>
      <div className="min-w-0">
        <div className="text-3xl font-bold leading-none tabular-nums">{value}</div>
        <div className="mt-1 text-sm text-text-2">{label}</div>
        {hint && <div className="text-xs text-text-2">{hint}</div>}
      </div>
    </div>
  );
}

export function EmptyState({ title, hint }: { title: string; hint?: string }) {
  return (
    <div className="card grid place-items-center gap-1 p-10 text-center">
      <Inbox size={32} className="text-text-2" aria-hidden />
      <p className="font-bold">{title}</p>
      {hint && <p className="text-text-2">{hint}</p>}
    </div>
  );
}

export function ErrorState({ message, onRetry, retryLabel }: {
  message: string; onRetry: () => void; retryLabel: string;
}) {
  return (
    <div role="alert" className="card flex items-center gap-3 border-overdue p-4 text-overdue">
      <AlertTriangle size={20} aria-hidden />
      <span className="flex-1">{message}</span>
      <button onClick={onRetry} className="inline-flex items-center gap-1 rounded-lg border border-border px-3 py-1.5 font-bold">
        <RotateCw size={14} aria-hidden /> {retryLabel}
      </button>
    </div>
  );
}

export function Skeleton({ rows = 4 }: { rows?: number }) {
  return (
    <div className="grid gap-2" aria-busy="true">
      {Array.from({ length: rows }, (_, i) => (
        <div key={i} className="h-14 animate-pulse rounded-xl bg-surface-2" />
      ))}
    </div>
  );
}

export const fmtDate = (d: string) =>
  new Date(d).toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" });

/** "12 days left" / "3 days overdue" for an obligation. */
export function daysText(n: number | null) {
  if (n === null) return "";
  if (n < 0) return `${-n}d overdue`;
  return n === 0 ? "due today" : `${n}d left`;
}
