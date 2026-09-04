"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { getSettlementDetail, getSettlements, type SettlementDetail, type SettlementRecord } from "@/lib/api";
import { formatDate, formatINR } from "@/lib/utils";

const navigation = [
  { label: "Overview", href: "/" },
  { label: "Reconciliation", href: "/exceptions" },
  { label: "Settlements", href: "/settlements" },
  { label: "Transactions", href: "/transactions" },
  { label: "AI Copilot", href: "/copilot" },
];

const settlementStatuses = ["processed", "processing", "on_hold"];

function statusLabel(value: string): string {
  return value.replaceAll("_", " ").replace(/\b\w/g, (character) => character.toUpperCase());
}

function statusClass(status: string): string {
  if (status === "processed") return "bg-status-success-bg text-status-success";
  if (status === "on_hold") return "bg-status-critical-bg text-status-critical";
  return "bg-status-warning-bg text-status-warning";
}

function dateLabel(value: string | null): string {
  return value ? formatDate(value) : "Not processed";
}

function amount(value: number | string): string {
  return formatINR(Number(value));
}

function DetailPanel({ detail, onClose }: { detail: SettlementDetail; onClose: () => void }) {
  return <aside className="rounded-lg border border-border-subtle bg-surface-card p-5 shadow-sm" aria-label="Settlement detail">
    <div className="flex items-start justify-between gap-4 border-b border-border-subtle pb-4"><div><p className="font-mono text-[11px] uppercase tracking-[0.12em] text-text-muted">Settlement detail</p><h2 className="mt-1 font-display text-headline-md">{detail.razorpay_settlement_id}</h2></div><button aria-label="Close settlement detail" className="rounded bg-surface-subtle px-3 py-2 text-sm font-semibold text-text-secondary hover:bg-surface-container-high" onClick={onClose} type="button">Close</button></div>
    <div className="grid gap-4 py-5 sm:grid-cols-3"><div><p className="font-mono text-[11px] uppercase text-text-muted">Amount</p><p className="mt-1 font-display text-financial-metric-md">{amount(detail.amount)}</p></div><div><p className="font-mono text-[11px] uppercase text-text-muted">Expected</p><p className="mt-1 text-sm font-semibold">{dateLabel(detail.expected_date)}</p></div><div><p className="font-mono text-[11px] uppercase text-text-muted">Processed</p><p className="mt-1 text-sm font-semibold">{dateLabel(detail.processed_date)}</p></div></div>
    <div className="grid gap-5 border-t border-border-subtle pt-5 lg:grid-cols-2"><div><h3 className="font-display text-headline-sm">Settlement items <span className="font-mono text-xs font-normal text-text-muted">({detail.items.length})</span></h3>{detail.items.length === 0 ? <p className="mt-3 text-sm text-text-secondary">No settlement items returned.</p> : <ul className="mt-3 divide-y divide-border-subtle">{detail.items.map((item) => <li className="flex items-center justify-between gap-3 py-3 text-sm" key={item.id}><div><p className="font-medium">{statusLabel(item.entry_type)}</p><p className="font-mono text-[11px] text-text-muted">{item.payment_id ?? item.refund_id ?? "No linked reference"}</p></div><span className="font-mono text-xs font-semibold">{amount(item.amount)}</span></li>)}</ul>}</div><div><h3 className="font-display text-headline-sm">Bank credits <span className="font-mono text-xs font-normal text-text-muted">({detail.bank_transactions.length})</span></h3>{detail.bank_transactions.length === 0 ? <p className="mt-3 text-sm text-text-secondary">No bank transactions returned.</p> : <ul className="mt-3 divide-y divide-border-subtle">{detail.bank_transactions.map((transaction) => <li className="flex items-center justify-between gap-3 py-3 text-sm" key={transaction.id}><div><p className="font-medium">{transaction.bank_reference}</p><p className="font-mono text-[11px] text-text-muted">{dateLabel(transaction.credited_date)}</p></div><span className="font-mono text-xs font-semibold">{amount(transaction.amount)}</span></li>)}</ul>}</div></div>
  </aside>;
}

export default function SettlementsPage() {
  const [settlements, setSettlements] = useState<SettlementRecord[]>([]);
  const [status, setStatus] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [detail, setDetail] = useState<SettlementDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    getSettlements({ status, date_from: dateFrom, date_to: dateTo }, controller.signal)
      .then(setSettlements)
      .catch((requestError: unknown) => { if (!controller.signal.aborted) setError(requestError instanceof Error ? requestError.message : "Unable to load settlements."); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [dateFrom, dateTo, status]);

  async function openDetail(settlementId: number) {
    setSelectedId(settlementId);
    setDetail(null);
    setDetailError(null);
    setDetailLoading(true);
    try {
      setDetail(await getSettlementDetail(settlementId));
    } catch (requestError: unknown) {
      setDetailError(requestError instanceof Error ? requestError.message : "Unable to load settlement detail.");
    } finally {
      setDetailLoading(false);
    }
  }

  return <main className="min-h-screen bg-background text-text-primary">
    <header className="border-b border-border-subtle bg-surface-card"><div className="mx-auto flex max-w-[1440px] flex-col gap-4 px-4 py-4 sm:px-6 lg:flex-row lg:items-center lg:justify-between lg:px-8"><div><div className="flex items-center gap-2"><span className="font-display text-xl font-bold tracking-tight">ReconAI</span><span className="rounded bg-surface-subtle px-2 py-1 font-mono text-[10px] text-text-secondary">B2B</span></div><p className="mt-1 flex items-center gap-2 font-mono text-[11px] text-text-muted"><span className="h-1.5 w-1.5 rounded-full bg-status-success" />Razorpay connected</p></div><nav aria-label="Primary" className="flex max-w-full gap-1 overflow-x-auto rounded-lg bg-surface-container-low p-1">{navigation.map((item, index) => <Link className={`whitespace-nowrap rounded px-3 py-2 text-sm font-medium ${index === 2 ? "bg-primary-container text-on-primary" : "text-text-secondary hover:bg-surface-container-high"}`} href={item.href} key={item.href}>{item.label}</Link>)}</nav></div></header>
    <div className="mx-auto max-w-[1440px] px-4 py-8 sm:px-6 lg:px-8"><div className="mb-8 flex flex-col justify-between gap-4 border-b border-border-subtle pb-6 sm:flex-row sm:items-end"><div><p className="font-mono text-xs uppercase tracking-[0.14em] text-secondary">Settlement intelligence</p><h1 className="mt-2 font-display text-headline-xl">Settlements</h1><p className="mt-2 text-sm text-text-secondary">Monitor payout batches from expected date through bank processing.</p></div><Link className="text-sm font-semibold text-secondary hover:underline" href="/">Back to overview</Link></div>
      <section aria-label="Settlement filters" className="mb-6 rounded-lg border border-border-subtle bg-surface-card p-4 shadow-sm"><div className="grid gap-4 md:grid-cols-3"><label className="flex flex-col gap-2 text-sm font-medium text-text-secondary">Status<select className="rounded border border-border-strong bg-surface-card px-3 py-2 text-sm text-text-primary" onChange={(event) => setStatus(event.target.value)} value={status}><option value="">All statuses</option>{settlementStatuses.map((value) => <option key={value} value={value}>{statusLabel(value)}</option>)}</select></label><label className="flex flex-col gap-2 text-sm font-medium text-text-secondary">Expected from<input className="rounded border border-border-strong bg-surface-card px-3 py-2 text-sm text-text-primary" onChange={(event) => setDateFrom(event.target.value)} type="date" value={dateFrom} /></label><label className="flex flex-col gap-2 text-sm font-medium text-text-secondary">Expected through<input className="rounded border border-border-strong bg-surface-card px-3 py-2 text-sm text-text-primary" onChange={(event) => setDateTo(event.target.value)} type="date" value={dateTo} /></label></div></section>
      {error && <div className="mb-6 rounded-lg border border-status-critical-border bg-status-critical-bg p-4 text-sm text-status-critical" role="alert"><div className="flex flex-wrap items-center justify-between gap-3"><span>{error}</span><button className="rounded bg-primary px-3 py-2 font-semibold text-on-primary" onClick={() => window.location.reload()} type="button">Try again</button></div></div>}
      {loading ? <div className="rounded-lg border border-border-subtle bg-surface-card p-10 text-center text-text-secondary">Loading settlements...</div> : settlements.length === 0 ? <div className="rounded-lg border border-status-success-border bg-status-success-bg p-8 text-center"><h2 className="font-display text-headline-sm text-status-success">No settlements found</h2><p className="mt-2 text-sm text-text-secondary">No settlement batches match the selected filters.</p></div> : <div className="overflow-hidden rounded-lg border border-border-subtle bg-surface-card shadow-sm"><div className="overflow-x-auto"><table className="w-full min-w-[900px] border-collapse text-left"><thead className="bg-surface-subtle"><tr className="font-mono text-[11px] uppercase tracking-[0.1em] text-text-muted"><th className="px-5 py-3 font-medium">Settlement</th><th className="px-5 py-3 font-medium">Amount</th><th className="px-5 py-3 font-medium">Expected date</th><th className="px-5 py-3 font-medium">Processed date</th><th className="px-5 py-3 font-medium">Status</th><th className="px-5 py-3 font-medium">Delay</th><th className="px-5 py-3 text-right font-medium">Action</th></tr></thead><tbody className="divide-y divide-border-subtle">{settlements.map((settlement) => <tr className="hover:bg-surface-subtle/60" key={settlement.id}><td className="px-5 py-4"><p className="font-display font-semibold">{settlement.razorpay_settlement_id}</p><p className="mt-1 font-mono text-[11px] text-text-muted">{settlement.item_count} items</p></td><td className="px-5 py-4 font-mono text-sm font-semibold">{amount(settlement.amount)}</td><td className="px-5 py-4 text-sm">{dateLabel(settlement.expected_date)}</td><td className="px-5 py-4 text-sm text-text-secondary">{dateLabel(settlement.processed_date)}</td><td className="px-5 py-4"><span className={`rounded px-2 py-1 font-mono text-[11px] font-semibold uppercase ${statusClass(settlement.status)}`}>{statusLabel(settlement.status)}</span></td><td className="px-5 py-4">{settlement.days_overdue > 0 ? <span className="font-mono text-xs font-semibold text-status-critical">{settlement.days_overdue} days overdue</span> : <span className="text-sm text-text-muted">On schedule</span>}</td><td className="px-5 py-4 text-right"><button className="text-sm font-semibold text-secondary hover:underline" onClick={() => openDetail(settlement.id)} type="button">View detail</button></td></tr>)}</tbody></table></div></div>}
      {selectedId !== null && <div className="mt-6">{detailLoading && <div className="rounded-lg border border-border-subtle bg-surface-card p-8 text-center text-text-secondary">Loading settlement detail...</div>}{detailError && <div className="rounded-lg border border-status-critical-border bg-status-critical-bg p-5 text-sm text-status-critical" role="alert">{detailError}</div>}{detail && <DetailPanel detail={detail} onClose={() => { setSelectedId(null); setDetail(null); }} />}</div>}
    </div>
  </main>;
}