export const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const KEY = "waymark.tokens";

export type Tokens = { access_token: string; refresh_token: string };

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

export const tokenStore = {
  get(): Tokens | null {
    try {
      return JSON.parse(localStorage.getItem(KEY) ?? "null");
    } catch {
      return null;
    }
  },
  set(t: Tokens | null) {
    try {
      if (t) localStorage.setItem(KEY, JSON.stringify(t));
      else localStorage.removeItem(KEY);
    } catch {}
  },
};

async function raw(path: string, init: RequestInit, access?: string) {
  return fetch(`${API}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(access ? { Authorization: `Bearer ${access}` } : {}),
      ...init.headers,
    },
  });
}

/** Typed fetch against /api/v1 with one transparent refresh on 401. */
export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const t = tokenStore.get();
  let res = await raw(`/api/v1${path}`, init, t?.access_token);
  if (res.status === 401 && t?.refresh_token && !path.startsWith("/auth/")) {
    const r = await raw("/api/v1/auth/refresh", {
      method: "POST",
      body: JSON.stringify({ refresh_token: t.refresh_token }),
    });
    if (r.ok) {
      const next = { ...t, access_token: (await r.json()).access_token };
      tokenStore.set(next);
      res = await raw(`/api/v1${path}`, init, next.access_token);
    } else tokenStore.set(null);
  }
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new ApiError(res.status, body?.error?.message ?? res.statusText);
  }
  return res.json();
}

export const health = () => fetch(`${API}/health`).then((r) => r.json() as Promise<{ status: string }>);
