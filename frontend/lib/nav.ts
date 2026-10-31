import type { Role } from "./auth";

/** Role -> nav slugs (docs/05 §3). Label key is `nav.<slug>`. */
const COMMON = ["notifications"];
export const NAV: Record<Role, string[]> = {
  INSTITUTION: ["home", "applications", "documents", "obligations", "complaints", ...COMMON],
  SCRUTINY_OFFICER: ["work-queue", "applications", "documents", "obligations", ...COMMON],
  REGIONAL_OFFICER: [
    "pendency", "compliance", "obligations", "applications", "evc", "institutions", "complaints", "risk",
    ...COMMON,
  ],
  BUREAU_OFFICER: ["complaint-queue", "overlaps", "institutions", "complaint-dashboard", ...COMMON],
  ADMIN: [
    "pendency", "compliance", "obligations", "applications", "evc", "institutions", "complaint-queue",
    "overlaps",
    "complaint-dashboard", "risk", "config", "users", "audit", "demo", ...COMMON,
  ],
};
