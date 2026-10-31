"use client";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { BellRing, CheckCircle2, CircleDashed, Hourglass, MinusCircle, SkipForward, X } from "lucide-react";
import { useState } from "react";
import { daysText, EmptyState, ErrorState, fmtDate, PageHeader, Skeleton, StatusChip } from "@/components/ui";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";

type Obl = {
  id: string; title: string; type: string; status: string; due_at: string; days_remaining: number | null;
  institution: { name: string }; source: string; waive_reason: string | null; description: string | null;
  next_alert: { step: string; at: string } | null;
  alerts_sent: { step: string; status: string; sent_at: string }[];
  ladder?: { key: string; days_offset: number; notify: string[] }[];
};
type Dlg = { action: "fulfil" | "waive" | "extend"; } | null;
const FILTERS = ["", "OVERDUE", "DUE_SOON", "UPCOMING", "FULFILLED", "WAIVED", "PAUSED"];
const pretty = (s: string) => s.replace(/_/g, " ").toLowerCase().replace(/^\w/, (c) => c.toUpperCase());
const tone = (s: string) => (s === "OVERDUE" ? "var(--overdue)" : s === "DUE_SOON" ? "var(--due-soon)" : "var(--border)");

function Ladder({ o }: { o: Obl }) {
  return (
    <ol className="mt-2" aria-label="Escalation ladder">
      {o.ladder?.map((s, i) => {
        const log = o.alerts_sent.find((a) => a.step === s.key);
        const next = o.next_alert?.step === s.key;
        const Icon = log ? (log.status === "SENT" ? BellRing : SkipForward) : next ? Hourglass : CircleDashed;
        const color = log?.status === "SENT" ? "var(--fulfilled)" : next ? "var(--due-soon)" : "var(--muted)";
        return (
          <li key={s.key} className="relative flex gap-3 pb-4 last:pb-0">
            {i < o.ladder!.length - 1 && <span className="absolute left-3.5 top-7 h-full w-px bg-border" aria-hidden />}
            <span className="z-10 grid size-7 shrink-0 place-items-center rounded-full bg-surface-2" style={{ color }}>
              <Icon size={15} aria-hidden />
            </span>
            <div className="text-sm">
              <div className="font-bold">{s.key} <span className="font-normal text-text-2">→ {s.notify.map(pretty).join(", ")}</span></div>
              <div className="text-text-2">
                {log ? `${log.status === "SENT" ? "Sent" : "Skipped"} ${fmtDate(log.sent_at)}` : next ? `Next · ${fmtDate(o.next_alert!.at)}` : "Pending"}
              </div>
            </div>
          </li>
        );
      })}
    </ol>
  );
}

function ActionDialog({ id, action, onClose }: { id: string; action: "fulfil" | "waive" | "extend"; onClose: () => void }) {
  const qc = useQueryClient();
  const [text, setText] = useState("");
  const [date, setDate] = useState("");
  const meta = {
    fulfil: { title: "Mark as fulfilled", label: "Note (optional)", cta: "Fulfil", need: false },
    waive: { title: "Waive obligation", label: "Reason for waiver (required)", cta: "Waive", need: true },
    extend: { title: "Extend due date", label: "Reason for extension (required)", cta: "Extend", need: true },
  }[action];
  const m = useMutation({
    mutationFn: () => api(`/obligations/${id}/${action}`, {
      method: "POST",
      body: JSON.stringify(action === "fulfil" ? { note: text } : action === "waive" ? { reason: text }
        : { new_due_at: new Date(date).toISOString(), reason: text }),
    }),
    onSuccess: async () => { await qc.invalidateQueries(); onClose(); },
  });
  const valid = (!meta.need || text.trim().length >= 5) && (action !== "extend" || !!date);
  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-black/50 p-4" onKeyDown={(e) => e.key === "Escape" && onClose()}>
      <form role="dialog" aria-modal="true" aria-label={meta.title} className="card w-full max-w-md space-y-4 p-5"
        onSubmit={(e) => { e.preventDefault(); if (valid) m.mutate(); }}>
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold">{meta.title}</h2>
          <button type="button" aria-label="Close" onClick={onClose} className="grid size-11 place-items-center"><X /></button>
        </div>
        {action === "extend" && (
          <label className="block font-bold">New due date
            <input type="date" required autoFocus value={date} onChange={(e) => setDate(e.target.value)}
              className="mt-1 min-h-11 w-full rounded-lg border border-border bg-surface px-3 font-normal" />
          </label>
        )}
        <label className="block font-bold">{meta.label}
          <textarea rows={3} autoFocus={action !== "extend"} value={text} onChange={(e) => setText(e.target.value)}
            className="mt-1 w-full rounded-lg border border-border bg-surface px-3 py-2 font-normal" />
          {meta.need && text.length > 0 && text.trim().length < 5 && <span className="text-sm font-normal text-overdue">At least 5 characters.</span>}
        </label>
        {m.error && <p role="alert" className="font-bold text-overdue">{(m.error as Error).message}</p>}
        <div className="flex justify-end gap-2">
          <button type="button" onClick={onClose} className="min-h-11 rounded-lg border border-border px-4 font-bold">Cancel</button>
          <button disabled={!valid || m.isPending} className="min-h-11 rounded-lg bg-primary px-4 font-bold text-white disabled:opacity-50">
            {m.isPending ? "Saving…" : meta.cta}
          </button>
        </div>
      </form>
    </div>
  );
}

export default function Obligations() {
  const { t, user } = useAuth();
  const [status, setStatus] = useState("");
  const [openId, setOpenId] = useState<string | null>(null);
  const [dlg, setDlg] = useState<Dlg>(null);
  const list = useQuery({
    queryKey: ["obligations", status],
    queryFn: () => api<{ items: Obl[] }>(`/obligations?page_size=200${status ? `&status=${status}` : ""}`),
  });
  const detail = useQuery({ queryKey: ["obligation", openId], enabled: !!openId, queryFn: () => api<Obl>(`/obligations/${openId}`) });
  const d = detail.data;
  const canClose = user && user.role !== "BUREAU_OFFICER";
  const regional = user && (user.role === "REGIONAL_OFFICER" || user.role === "ADMIN");
  const open = d && d.status !== "FULFILLED" && d.status !== "WAIVED";

  return (
    <>
      <PageHeader title={t("nav.obligations")} subtitle="Every time-bound requirement in one list" />
      <div role="group" aria-label="Filter by status" className="mb-4 flex flex-wrap gap-2">
        {FILTERS.map((s) => (
          <button key={s} aria-pressed={status === s} onClick={() => setStatus(s)}
            className={`min-h-11 rounded-full border px-4 font-bold ${status === s ? "border-primary bg-primary text-white" : "border-border bg-surface text-text-2 hover:border-primary"}`}>
            {s ? pretty(s) : "All"}
          </button>
        ))}
      </div>
      {list.isLoading && <Skeleton rows={5} />}
      {list.error && <ErrorState message={t("state.error")} onRetry={() => list.refetch()} retryLabel={t("state.retry")} />}
      {list.data?.items.length === 0 && <EmptyState title={t("state.empty")} hint="Try another status filter." />}
      <div className={`grid items-start gap-5 ${d ? "xl:grid-cols-[1.6fr_1fr]" : ""}`}>
        <ul className="grid gap-2">
          {list.data?.items.map((o) => (
            <li key={o.id}>
              <button onClick={() => setOpenId(o.id)} aria-pressed={openId === o.id}
                className={`card flex w-full flex-wrap items-center gap-x-4 gap-y-1 p-3 text-left hover:border-primary ${openId === o.id ? "ring-2 ring-primary" : ""}`}>
                <span className="size-2.5 shrink-0 rounded-full" style={{ background: tone(o.status) }} aria-hidden />
                <div className="min-w-0 flex-1 basis-56">
                  <div className="font-bold">{o.title}</div>
                  <div className="truncate text-sm text-text-2">{o.institution.name} · {pretty(o.type)}</div>
                </div>
                <div className="text-sm text-text-2">Due {fmtDate(o.due_at)}</div>
                <div className="flex items-center gap-2">
                  <StatusChip status={o.status} />
                  <span className="w-20 text-right text-sm font-bold tabular-nums">{daysText(o.days_remaining)}</span>
                </div>
              </button>
            </li>
          ))}
        </ul>
        {openId && (
          <aside aria-label="Obligation detail" className="card rise p-5 xl:sticky xl:top-20">
            {detail.isLoading && <Skeleton rows={3} />}
            {d && (
              <>
                <div className="flex items-start justify-between gap-2">
                  <h2 className="text-lg font-bold">{d.title}</h2>
                  <button aria-label="Close detail" onClick={() => setOpenId(null)} className="grid size-9 place-items-center"><X size={18} /></button>
                </div>
                <p className="text-text-2">{d.institution.name}</p>
                <div className="mt-2 flex flex-wrap items-center gap-2"><StatusChip status={d.status} />
                  <span className="text-sm text-text-2">Due {fmtDate(d.due_at)} · {pretty(d.source)}</span></div>
                {d.waive_reason && (
                  <p className="mt-3 flex gap-2 rounded-lg bg-surface-2 p-3 text-sm"><MinusCircle size={16} className="mt-0.5 shrink-0" aria-hidden />{d.waive_reason}</p>
                )}
                {open && (
                  <div className="mt-4 flex flex-wrap gap-2">
                    {canClose && <button onClick={() => setDlg({ action: "fulfil" })} className="inline-flex min-h-11 items-center gap-2 rounded-lg bg-primary px-4 font-bold text-white"><CheckCircle2 size={16} aria-hidden /> Fulfil</button>}
                    {regional && <button onClick={() => setDlg({ action: "extend" })} className="min-h-11 rounded-lg border border-border px-4 font-bold">Extend</button>}
                    {regional && <button onClick={() => setDlg({ action: "waive" })} className="min-h-11 rounded-lg border border-border px-4 font-bold">Waive</button>}
                  </div>
                )}
                <h3 className="mt-5 text-sm font-bold uppercase tracking-wide text-text-2">Escalation ladder</h3>
                <Ladder o={d} />
              </>
            )}
          </aside>
        )}
      </div>
      {dlg && openId && <ActionDialog id={openId} action={dlg.action} onClose={() => setDlg(null)} />}
    </>
  );
}
