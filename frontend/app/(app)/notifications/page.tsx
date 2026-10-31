"use client";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { BellRing, Check } from "lucide-react";
import { EmptyState, ErrorState, fmtDate, PageHeader, Skeleton } from "@/components/ui";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";

type N = { id: string; subject: string; body: string; read_at: string | null; created_at: string };

export default function Notifications() {
  const { t } = useAuth();
  const qc = useQueryClient();
  const q = useQuery({
    queryKey: ["notifications", "all"],
    queryFn: () => api<{ unread_count: number; items: N[] }>("/notifications"),
  });
  const read = useMutation({
    mutationFn: (id: string) => api(`/notifications/${id}/read`, { method: "POST" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["notifications"] }),
  });
  return (
    <>
      <PageHeader title={t("nav.notifications")}
        subtitle={q.data ? (q.data.unread_count ? `${q.data.unread_count} unread` : "You're all caught up") : undefined} />
      {q.isLoading && <Skeleton rows={4} />}
      {q.error && <ErrorState message={t("state.error")} onRetry={() => q.refetch()} retryLabel={t("state.retry")} />}
      {q.data?.items.length === 0 && <EmptyState title={t("state.empty")} hint="Alerts from the obligation engine land here." />}
      <ul className="grid max-w-3xl gap-2">
        {q.data?.items.map((n) => (
          <li key={n.id} className={`card flex items-start gap-3 p-4 ${n.read_at ? "opacity-75" : ""}`}>
            <span className="relative mt-0.5 text-primary"><BellRing size={20} aria-hidden />{!n.read_at && <span className="absolute -right-1 -top-1 size-2.5 rounded-full bg-[var(--overdue)]" aria-label="Unread" />}</span>
            <div className="flex-1">
              <div className={n.read_at ? "" : "font-bold"}>{n.subject}</div>
              <div className="text-text-2">{n.body}</div>
              <div className="mt-1 text-xs text-text-2">{fmtDate(n.created_at)}</div>
            </div>
            {!n.read_at && (
              <button onClick={() => read.mutate(n.id)} className="inline-flex min-h-11 shrink-0 items-center gap-1 rounded-lg border border-border px-3 font-bold">
                <Check size={15} aria-hidden /> Mark read
              </button>
            )}
          </li>
        ))}
      </ul>
    </>
  );
}
