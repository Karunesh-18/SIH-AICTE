"use client";
import { createContext, useCallback, useContext, useEffect, useState } from "react";
import en from "./i18n/en.json";
import hi from "./i18n/hi.json";
import { api, tokenStore, type Tokens } from "./api";

export type Role = "INSTITUTION" | "SCRUTINY_OFFICER" | "REGIONAL_OFFICER" | "BUREAU_OFFICER" | "ADMIN";
export type User = {
  id: string; email: string; full_name: string; role: Role;
  institution_id: string | null; region_id: string | null; bureau_id: string | null;
  language: "en" | "hi";
};

type Ctx = {
  user: User | null;
  ready: boolean;
  lang: "en" | "hi";
  t: (k: string) => string;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  setLang: (l: "en" | "hi") => void;
};

const AuthCtx = createContext<Ctx>(null as unknown as Ctx);
export const useAuth = () => useContext(AuthCtx);
const dict = { en, hi } as Record<string, Record<string, string>>;

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [ready, setReady] = useState(false);
  const [lang, setLangState] = useState<"en" | "hi">("en");

  useEffect(() => {
    if (!tokenStore.get()) return setReady(true);
    api<User>("/auth/me")
      .then((u) => { setUser(u); setLangState(u.language); })
      .catch(() => tokenStore.set(null))
      .finally(() => setReady(true));
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const r = await api<Tokens & { user: User }>("/auth/login", {
      method: "POST", body: JSON.stringify({ email, password }),
    });
    tokenStore.set({ access_token: r.access_token, refresh_token: r.refresh_token });
    setUser(r.user);
    setLangState(r.user.language);
  }, []);

  const logout = useCallback(() => { tokenStore.set(null); setUser(null); }, []);

  const setLang = useCallback((l: "en" | "hi") => {
    setLangState(l);
    if (tokenStore.get()) api("/auth/me", { method: "PATCH", body: JSON.stringify({ language: l }) }).catch(() => {});
  }, []);

  const t = useCallback((k: string) => dict[lang][k] ?? en[k as keyof typeof en] ?? k, [lang]);

  return (
    <AuthCtx.Provider value={{ user, ready, lang, t, login, logout, setLang }}>{children}</AuthCtx.Provider>
  );
}
