"use client";
import { use } from "react";
import { EmptyState, PageHeader } from "@/components/ui";
import { useAuth } from "@/lib/auth";

// Placeholder for nav targets built in later phases.
export default function Section({ params }: { params: Promise<{ section: string }> }) {
  const { section } = use(params);
  const { t } = useAuth();
  return (
    <>
      <PageHeader title={t(`nav.${section}`)} />
      <EmptyState title={t("later")} hint="This module is on the build plan and arrives in an upcoming phase." />
    </>
  );
}
