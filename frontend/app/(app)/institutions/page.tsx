"use client";
import { useQuery } from "@tanstack/react-query";
import { Building2, FlaskConical, GraduationCap, MapPin, Search, Briefcase } from "lucide-react";
import { useState } from "react";
import { EmptyState, ErrorState, PageHeader, Skeleton } from "@/components/ui";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";

type Inst = {
  id: string; aicte_code: string; name: string; type: string; state: string; city: string; status: string;
};
type Page = { items: Inst[]; total: number };
const TYPE_ICON = { ENGINEERING: GraduationCap, MANAGEMENT: Briefcase, PHARMACY: FlaskConical, OTHER: Building2 } as const;
const pretty = (s: string) => s.toLowerCase().replace(/^\w/, (c) => c.toUpperCase());

export default function Institutions() {
  const { t } = useAuth();
  const [q, setQ] = useState("");
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["institutions", q],
    queryFn: () => api<Page>(`/institutions?page_size=100&q=${encodeURIComponent(q)}`),
  });

  return (
    <>
      <PageHeader title={t("nav.institutions")} subtitle={data ? `${data.total} institutions in your scope` : undefined} />
      <label className="relative mb-5 block max-w-md">
        <span className="sr-only">Search</span>
        <Search size={18} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-text-2" aria-hidden />
        <input placeholder="Search name or code" value={q} onChange={(e) => setQ(e.target.value)}
          className="min-h-11 w-full rounded-lg border border-border bg-surface pl-10 pr-3" />
      </label>
      {isLoading && <Skeleton rows={5} />}
      {error && <ErrorState message={t("state.error")} onRetry={() => refetch()} retryLabel={t("state.retry")} />}
      {data?.items.length === 0 && <EmptyState title={t("state.empty")} hint="No institution matches this search." />}
      <ul className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        {data?.items.map((i) => {
          const Icon = TYPE_ICON[i.type as keyof typeof TYPE_ICON] ?? Building2;
          return (
            <li key={i.id} className="card rise flex gap-3 p-4">
              <span className="grid size-11 shrink-0 place-items-center rounded-xl bg-primary-soft text-primary"><Icon size={22} aria-hidden /></span>
              <div className="min-w-0">
                <div className="font-bold leading-snug">{i.name}</div>
                <div className="mt-0.5 flex items-center gap-1 text-sm text-text-2"><MapPin size={14} aria-hidden /> {i.city}, {i.state}</div>
                <div className="mt-2 flex flex-wrap gap-2 text-xs font-bold">
                  <span className="rounded-full bg-surface-2 px-2.5 py-0.5">{i.aicte_code}</span>
                  <span className="rounded-full bg-surface-2 px-2.5 py-0.5">{pretty(i.type)}</span>
                  {i.status !== "ACTIVE" && <span className="rounded-full bg-[var(--due-soon-bg)] px-2.5 py-0.5 text-due-soon">Under review</span>}
                </div>
              </div>
            </li>
          );
        })}
      </ul>
    </>
  );
}
