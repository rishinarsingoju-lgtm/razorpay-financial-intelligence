import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

test("frontend package exposes startup checks", () => {
  const packageJson = JSON.parse(readFileSync(new URL("../package.json", import.meta.url), "utf8"));

  assert.equal(packageJson.scripts.dev, "next dev --hostname 127.0.0.1 --port 3000");
  assert.equal(packageJson.scripts.typecheck, "tsc --noEmit");
});

test("phase 1 shell is present", () => {
  const page = readFileSync(new URL("../src/app/page.tsx", import.meta.url), "utf8");

  assert.match(page, /Financial Intelligence Foundation/);
  assert.match(page, /SQLAlchemy models and Alembic migration ready/);
});
