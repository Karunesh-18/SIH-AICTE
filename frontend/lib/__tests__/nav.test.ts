import { expect, test } from "vitest";
import { NAV } from "../nav";

test("each role has its own nav and only admin sees audit", () => {
  expect(Object.keys(NAV)).toHaveLength(5);
  for (const [role, items] of Object.entries(NAV)) {
    expect(items.includes("audit")).toBe(role === "ADMIN");
  }
  expect(NAV.INSTITUTION).not.toContain("risk");
});
