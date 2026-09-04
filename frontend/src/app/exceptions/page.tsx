"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { getExceptions, updateExceptionStatus, type ExceptionRecord } from "@/lib/api";
import { formatDateTime, formatINR } from "@/lib/utils";

const navigation = [
  { label: "Overview", href: "/" },
  { label: "Reconciliation", href: "/exceptions" },
  { label: "Settlements", href: "/settlements" },
  { label: "Transactions", href: "/transactions" },
  { label: "AI Copilot", href: "/copilot" },
];

const exceptionTypes = [
  ["delayed_settlement", "Delayed settlement"],
  ["missing_settlement", "Missing settlement"],
  ["partial_settlement", "Partial settlement"],
  ["duplicate", "Duplicate"],
  ["fee_mismatch", "Fee mismatch"],
  ["bank_credit_mismatch", "Bank-credit mismatch"],
  ["unusual_pattern", "Unusual pattern"],
];

const statuses = ["open", "investigating", "resolved"];

function titleCase(value: string): string {
  return value.replaceAll("_", " ").replace(/\b\w/g, (character) => character.toUpperCase());
}

function amount(value: number | string | null): string {
  return value === null ? "Not provided" : formatINR(Number(value));
}

function severityClass(severity: string): string {
  if (severity === "critical") return "bg-status-critical-bg text-status-critical";
  if (severity === "warning") return "bg-status-warning-bg text-status-warning";
  return "bg-surface-subtle text-text-secondary";
}

function statusClass(status: string): string {
  if (status === "resolved") return "bg-status-success-bg text-status-success";
  if (status === "investigating") return "bg-status-investigating-bg text-status-investigating";
  return "bg-status-critical-bg text-status-critical";
}

export default function ExceptionsPage() {
  const [exceptions, setExceptions] = useState<ExceptionRecord[]>([]);
  const [type, setType] = useState("");
  const [severity, setSeverity] = useState("");
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [updatingId, setUpdatingId] = useState<number | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    getExceptions({ type, severity, status }, controller.signal)
      .then(setExceptions)
      .catch((requestError: unknown) => {
        if (!controller.signal.aborted) setError(requestError instanceof Error ? requestError.message : "Unable to load exceptions.");
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [severity, status, type]);

  async function changeStatus(exceptionId: number, nextStatus: string) {
    setUpdatingId(exceptionId);
    setError(null);
    try {
      await updateExceptionStatus(exceptionId, nextStatus);
      setExceptions((current) => current.map((exception) => exception.id === exceptionId ? { ...exception, status: nextStatus } : exception));
    } catch (requestError: unknown) {
      setError(requestError instanceof Error ? requestError.message : "Unable to update exception status.");
    } finally {
      setUpdatingId(null);
    }
  }

  return (
    <main className="min-h-screen bg-background text-text-primary">
      <header className="border-b border-border-subtle bg-surface-card">
        <div className="mx-auto flex max-w-[1440px] flex-col gap-4 px-4 py-4 sm:px-6 lg:flex-row lg:items-center lg:justify-between lg:px-8">
          <div>
            <div className="flex items-center gap-2"><span className="font-display text-xl font-bold tracking-tight">ReconAI</span><span className="rounded bg-surface-subtle px-2 py-1 font-mono text-[10px] text-text-secondary">B2B</span></div>
            <p className="mt-1 flex items-center gap-2 font-mono text-[11px] text-text-muted"><span className="h-1.5 w-1.5 rounded-full bg-status-success" />Razorpay connected</p>
          </div>
          <nav aria-label="Primary" className="flex max-w-full gap-1 overflow-x-auto rounded-lg bg-surface-container-low p-1">
            {navigation.map((item, index) => <Link className={`whitespace-nowrap rounded px-3 py-2 text-sm font-medium ${index === 1 ? "bg-primary-container text-on-primary" : "text-text-secondary hover:bg-surface-container-high"}`} href={item.href} key={item.href}>{item.label}</Link>)}
          </nav>
        </div>
      </header>

      <div className="mx-auto max-w-[1440px] px-4 py-8 sm:px-6 lg:px-8">
        <div className="mb-8 flex flex-col justify-between gap-4 border-b border-border-subtle pb-6 sm:flex-row sm:items-end">
          <div><p className="font-mono text-xs uppercase tracking-[0.14em] text-secondary">Reconciliation control</p><h1 className="mt-2 font-display text-headline-xl">Exceptions</h1><p className="mt-2 text-sm text-text-secondary">Review breaks in the payment-to-settlement ledger and move them through investigation.</p></div>
          <Link className="text-sm font-semibold text-secondary hover:underline" href="/">Back to overview</Link>
        </div>

        <section aria-label="Exception filters" className="mb-6 rounded-lg border border-border-subtle bg-surface-card p-4 shadow-sm">
          <div className="grid gap-4 md:grid-cols-3">
            <label className="flex flex-col gap-2 text-sm font-medium text-text-secondary">Exception type<select className="rounded border border-border-strong bg-surface-card px-3 py-2 text-sm text-text-primary" onChange={(event) => setType(event.target.value)} value={type}><option value="">All types</option>{exceptionTypes.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
            <label className="flex flex-col gap-2 text-sm font-medium text-text-secondary">Severity<select className="rounded border border-border-strong bg-surface-card px-3 py-2 text-sm text-text-primary" onChange={(event) => setSeverity(event.target.value)} value={severity}><option value="">All severities</option><option value="critical">Critical</option><option value="warning">Warning</option><option value="info">Info</option></select></label>
            <label className="flex flex-col gap-2 text-sm font-medium text-text-secondary">Status<select className="rounded border border-border-strong bg-surface-card px-3 py-2 text-sm text-text-primary" onChange={(event) => setStatus(event.target.value)} value={status}><option value="">All statuses</option>{statuses.map((value) => <option key={value} value={value}>{titleCase(value)}</option>)}</select></label>
          </div>
        </section>

        {error && <div className="mb-6 rounded-lg border border-status-critical-border bg-status-critical-bg p-4 text-sm text-status-critical" role="alert"><div className="flex flex-wrap items-center justify-between gap-3"><span>{error}</span><button className="rounded bg-primary px-3 py-2 font-semibold text-on-primary" onClick={() => window.location.reload()} type="button">Try again</button></div></div>}

        {loading ? <div className="rounded-lg border border-border-subtle bg-surface-card p-10 text-center text-text-secondary">Loading exceptions...</div> : exceptions.length === 0 ? <div className="rounded-lg border border-status-success-border bg-status-success-bg p-8 text-center"><h2 className="font-display text-headline-sm text-status-success">No exceptions found</h2><p className="mt-2 text-sm text-text-secondary">No reconciliation exceptions match the selected filters.</p></div> : <div className="overflow-hidden rounded-lg border border-border-subtle bg-surface-card shadow-sm"><div className="overflow-x-auto"><table className="w-full min-w-[1060px] border-collapse text-left"><thead className="bg-surface-subtle"><tr className="font-mono text-[11px] uppercase tracking-[0.1em] text-text-muted"><th className="px-5 py-3 font-medium">Exception</th><th className="px-5 py-3 font-medium">Severity</th><th className="px-5 py-3 font-medium">Expected / actual</th><th className="px-5 py-3 text-right font-medium">Variance</th><th className="px-5 py-3 font-medium">References</th><th className="px-5 py-3 font-medium">Detected</th><th className="px-5 py-3 font-medium">Status</th></tr></thead><tbody className="divide-y divide-border-subtle">{exceptions.map((exception) => <tr className="align-top hover:bg-surface-subtle/60" key={exception.id}><td className="px-5 py-4"><div className="flex items-start gap-3"><span className="mt-1 h-2 w-2 shrink-0 rounded-full bg-status-critical" /><div><p className="font-display font-semibold">{titleCase(exception.type)}</p><p className="mt-1 max-w-xs text-sm leading-5 text-text-secondary">{exception.description}</p><span className="mt-2 inline-block font-mono text-[11px] text-text-muted">EXC-{exception.id}</span></div></div></td><td className="px-5 py-4"><span className={`rounded px-2 py-1 font-mono text-[11px] font-semibold uppercase ${severityClass(exception.severity)}`}>{exception.severity}</span></td><td className="px-5 py-4 font-mono text-xs"><p>{amount(exception.expected_amount)}</p><p className="mt-1 text-text-muted">Actual: {amount(exception.actual_amount)}</p></td><td className={`px-5 py-4 text-right font-mono text-xs font-semibold ${Number(exception.discrepancy) > 0 ? "text-status-critical" : "text-text-primary"}`}>{amount(exception.discrepancy)}</td><td className="px-5 py-4 font-mono text-[11px] text-text-secondary"><p>{exception.related_payment_id ? <Link className="text-secondary hover:underline" href={`/transactions/${exception.related_payment_id}/chain`}>Payment: {exception.related_payment_id}</Link> : "Payment: Not linked"}</p><p className="mt-2">Order: {exception.related_order_id ?? "Not linked"}</p><p className="mt-2">Settlement: {exception.related_settlement_id ? <Link className="text-secondary hover:underline" href={`/settlements/${exception.related_settlement_id}`}>{exception.related_settlement_id}</Link> : "Not linked"}</p></td><td className="whitespace-nowrap px-5 py-4 font-mono text-[11px] text-text-secondary">{formatDateTime(exception.detected_at)}</td><td className="px-5 py-4"><select aria-label={`Update status for exception ${exception.id}`} className={`rounded px-2 py-1 font-mono text-[11px] font-semibold uppercase ${statusClass(exception.status)}`} disabled={updatingId === exception.id} onChange={(event) => changeStatus(exception.id, event.target.value)} value={exception.status}>{statuses.map((value) => <option key={value} value={value}>{value}</option>)}</select></td></tr>)}</tbody></table></div></div>}
      </div>
    </main>
  );
}