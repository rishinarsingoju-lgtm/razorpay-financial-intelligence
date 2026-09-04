import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

test("frontend package exposes startup checks", () => {
  const packageJson = JSON.parse(readFileSync(new URL("../package.json", import.meta.url), "utf8"));

  assert.equal(packageJson.scripts.dev, "next dev --hostname 127.0.0.1 --port 3000");
  assert.equal(packageJson.scripts.typecheck, "tsc --noEmit");
});

test("phase 5A dashboard is present", () => {
  const page = readFileSync(new URL("../src/app/page.tsx", import.meta.url), "utf8");

  assert.match(page, /getDashboardSummary/);
  assert.match(page, /Needs attention/);
  assert.match(page, /View all exceptions/);
});

test("phase 5B exceptions screen uses the exception API contract", () => {
  const page = readFileSync(new URL("../src/app/exceptions/page.tsx", import.meta.url), "utf8");

  assert.match(page, /getExceptions/);
  assert.match(page, /updateExceptionStatus/);
  assert.match(page, /Expected \/ actual/);
  assert.match(page, /transactions\/\$\{exception.related_payment_id\}\/chain/);
});

test("phase 5C settlements screen uses list and detail data", () => {
  const page = readFileSync(new URL("../src/app/settlements/page.tsx", import.meta.url), "utf8");

  assert.match(page, /getSettlements/);
  assert.match(page, /getSettlementDetail/);
  assert.match(page, /days_overdue/);
  assert.match(page, /Settlement items/);
  assert.match(page, /Bank credits/);
});

test("phase 5D transaction chain uses the chain API", () => {
  const page = readFileSync(new URL("../src/app/transactions/[paymentId]/chain/page.tsx", import.meta.url), "utf8");

  assert.match(page, /getTransactionChain/);
  assert.match(page, /Order/);
  assert.match(page, /Payment/);
  assert.match(page, /Settlement/);
  assert.match(page, /Bank credit/);
  assert.match(page, /No settlement returned/);
});
