"use client";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { useAuth } from "@/lib/auth";
import { NAV } from "@/lib/nav";

// Send each role to its first nav item (login if signed out).
export default function Root() {
  const { user, ready } = useAuth();
  const router = useRouter();
  useEffect(() => {
    if (!ready) return;
    router.replace(user ? `/${NAV[user.role][0]}` : "/login");
  }, [ready, user, router]);
  return null;
}
