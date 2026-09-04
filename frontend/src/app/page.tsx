"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { getDashboardSummary, type DashboardSummary } from "@/lib/api";
import { formatDate, formatINR } from "@/lib/utils";

const navigation = [
  { label: "Overview", href: "/" },
  { label: "Reconciliation", href: "/exceptions" },
  { label: "Settlements", href: "/settlements" },
  { label: "Transactions", href: "/transactions" },
  { label: "AI Copilot", href: "/copilot" },
];

function Metric({ label, value, detail, tone = "text-text-primary" }: { label: string; value: string; detail: string; tone?: string }) {
  return <article className="flex min-h-36 flex-col justify-between rounded-lg border border-border-subtle bg-surface-card p-5 shadow-sm"><p className="font-mono text-[11px] font-medium uppercase tracking-[0.14em] text-text-muted">{label}</p><div><p className={`mt-3 font-display text-financial-metric-lg ${tone}`}>{value}</p><p className="mt-1 text-sm text-text-secondary">{detail}</p></div></article>;
}

function DashboardContent() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const controller = new AbortController();
    getDashboardSummary(controller.signal).then(setSummary).catch((requestError: unknown) => {
      if (!controller.signal.aborted) setError(requestError instanceof Error ? requestError.message : "Unable to load dashboard data.");
    }).finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, []);

  if (loading) return <div className="rounded-lg border border-border-subtle bg-surface-card p-10 text-center text-text-secondary">Loading financial summary...</div>;
  if (error) return <div className="rounded-lg border border-status-critical-border bg-status-critical-bg p-6" role="alert"><h2 className="font-display text-headline-sm text-status-critical">Dashboard unavailable</h2><p className="mt-2 text-sm text-text-secondary">{error}</p><button className="mt-4 rounded bg-primary px-4 py-2 text-sm font-semibold text-on-primary" onClick={() => window.location.reload()} type="button">Try again</button></div>;
  if (!summary) return null;

  const { expected, settled, received } = summary.totals;
  const pending = Math.max(expected - settled, 0);
  const settlementRate = expected > 0 ? Math.min((settled / expected) * 100, 100) : 0;

  return <>
    <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <Metric label="Expected settlement" value={formatINR(expected)} detail="Net expected for today" />
      <Metric label="Settled amount" value={formatINR(settled)} detail={`${settlementRate.toFixed(1)}% of expected`} tone="text-status-success" />
      <Metric label="Bank received" value={formatINR(received)} detail="Credits recorded today" />
      <Metric label="Pending variance" value={formatINR(pending)} detail="Expected less settled" tone={pending > 0 ? "text-status-warning" : "text-status-success"} />
    </section>
    <section className="mt-8" aria-labelledby="attention-heading">
      <div className="mb-3 flex flex-wrap items-baseline justify-between gap-3"><div className="flex items-center gap-3"><span className="h-2.5 w-2.5 rounded-full bg-status-critical" aria-hidden="true" /><h2 className="font-display text-headline-md" id="attention-heading">Needs attention</h2><span className="rounded bg-status-critical-bg px-2 py-1 font-mono text-xs font-semibold text-status-critical">{summary.exception_count} active</span></div><Link className="text-sm font-semibold text-secondary hover:underline" href="/exceptions">View all exceptions</Link></div>
      {summary.top_exceptions.length === 0 ? <div className="rounded-lg border border-status-success-border bg-status-success-bg p-6 text-sm text-text-secondary">No open exceptions were returned for this account.</div> : <div className="grid gap-4 lg:grid-cols-3">{summary.top_exceptions.map((exception) => <article className="rounded-lg border border-border-subtle bg-surface-card p-5 shadow-sm" key={exception.id}><div className="flex items-center justify-between gap-3"><span className="rounded bg-status-warning-bg px-2 py-1 font-mono text-[11px] font-semibold uppercase text-status-warning">{exception.severity}</span><span className="font-mono text-[11px] text-text-muted">#{exception.id}</span></div><h3 className="mt-4 font-display text-headline-sm">{exception.type.replaceAll("_", " ")}</h3><p className="mt-2 text-sm leading-6 text-text-secondary">{exception.description}</p><Link className="mt-5 inline-block text-sm font-semibold text-secondary hover:underline" href={`/exceptions/${exception.id}`}>Investigate</Link></article>)}</div>}
    </section>
  </>;
}

export default function Home() {
  return (
    <main className="min-h-screen bg-background text-text-primary">
      <header className="border-b border-border-subtle bg-surface-card"><div className="mx-auto flex max-w-[1440px] flex-col gap-4 px-4 py-4 sm:px-6 lg:flex-row lg:items-center lg:justify-between lg:px-8"><div><div className="flex items-center gap-2"><span className="font-display text-xl font-bold tracking-tight">ReconAI</span><span className="rounded bg-surface-subtle px-2 py-1 font-mono text-[10px] text-text-secondary">B2B</span></div><p className="mt-1 flex items-center gap-2 font-mono text-[11px] text-text-muted"><span className="h-1.5 w-1.5 rounded-full bg-status-success" />Razorpay connected</p></div><nav aria-label="Primary" className="flex max-w-full gap-1 overflow-x-auto rounded-lg bg-surface-container-low p-1">{navigation.map((item, index) => <Link className={`whitespace-nowrap rounded px-3 py-2 text-sm font-medium ${index === 0 ? "bg-primary-container text-on-primary" : "text-text-secondary hover:bg-surface-container-high"}`} href={item.href} key={item.href}>{item.label}</Link>)}</nav></div></header>
      <div className="mx-auto max-w-[1440px] px-4 py-8 sm:px-6 lg:px-8"><div className="mb-8 flex flex-col justify-between gap-4 border-b border-border-subtle pb-6 sm:flex-row sm:items-end"><div><p className="font-mono text-xs uppercase tracking-[0.14em] text-secondary">Financial control center</p><h1 className="mt-2 font-display text-headline-xl">Overview</h1><p className="mt-2 text-sm text-text-secondary">A live view of expected, settled, and received funds.</p></div><p className="font-mono text-xs text-text-muted">As of {formatDate(new Date().toISOString().slice(0, 10))}</p></div><DashboardContent /></div>
    </main>
  );
}
