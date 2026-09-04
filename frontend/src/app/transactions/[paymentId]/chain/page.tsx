"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { getTransactionChain, type TransactionChain } from "@/lib/api";
import { formatDate, formatDateTime, formatINR } from "@/lib/utils";

type StageState = "complete" | "attention" | "missing";

function label(value: string): string {
  return value.replaceAll("_", " ").replace(/\b\w/g, (character) => character.toUpperCase());
}

function amount(value: number | string): string {
  return formatINR(Number(value));
}

function stateFor(stage: "order" | "payment" | "adjustment" | "settlement" | "bank", chain: TransactionChain): StageState {
  if (stage === "settlement") return chain.settlements.length === 0 ? "missing" : chain.settlements.some((item) => item.status !== "processed") ? "attention" : "complete";
  if (stage === "bank") return chain.bank_transactions.length === 0 ? "missing" : "complete";
  if (stage === "payment") return ["delayed", "missing", "fee_mismatch", "bank_mismatch", "duplicate_flagged", "held"].includes(chain.payment.reconciliation_status) ? "attention" : "complete";
  return "complete";
}

function stateStyles(state: StageState): { border: string; badge: string; label: string } {
  if (state === "missing") return { border: "border-status-critical-border", badge: "bg-status-critical-bg text-status-critical", label: "Missing" };
  if (state === "attention") return { border: "border-status-warning-border", badge: "bg-status-warning-bg text-status-warning", label: "Needs attention" };
  return { border: "border-status-success-border", badge: "bg-status-success-bg text-status-success", label: "Complete" };
}

function ChainStage({ title, state, children }: { title: string; state: StageState; children: React.ReactNode }) {
  const styles = stateStyles(state);
  return <article className={`rounded-lg border bg-surface-card p-5 shadow-sm ${styles.border}`}><div className="flex items-start justify-between gap-3"><h2 className="font-display text-headline-sm">{title}</h2><span className={`rounded px-2 py-1 font-mono text-[11px] font-semibold uppercase ${styles.badge}`}>{styles.label}</span></div><div className="mt-4 text-sm text-text-secondary">{children}</div></article>;
}

export default function TransactionChainPage() {
  const params = useParams<{ paymentId: string }>();
  const paymentId = params.paymentId;
  const [chain, setChain] = useState<TransactionChain | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    getTransactionChain(paymentId, controller.signal)
      .then(setChain)
      .catch((requestError: unknown) => { if (!controller.signal.aborted) setError(requestError instanceof Error ? requestError.message : "Unable to load transaction chain."); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [paymentId]);

  return <main className="min-h-screen bg-background text-text-primary"><header className="border-b border-border-subtle bg-surface-card"><div className="mx-auto flex max-w-[1440px] flex-col gap-4 px-4 py-4 sm:px-6 lg:flex-row lg:items-center lg:justify-between lg:px-8"><div><div className="flex items-center gap-2"><span className="font-display text-xl font-bold tracking-tight">ReconAI</span><span className="rounded bg-surface-subtle px-2 py-1 font-mono text-[10px] text-text-secondary">B2B</span></div><p className="mt-1 flex items-center gap-2 font-mono text-[11px] text-text-muted"><span className="h-1.5 w-1.5 rounded-full bg-status-success" />Razorpay connected</p></div><nav aria-label="Primary" className="flex max-w-full gap-1 overflow-x-auto rounded-lg bg-surface-container-low p-1"><Link className="whitespace-nowrap rounded px-3 py-2 text-sm font-medium text-text-secondary hover:bg-surface-container-high" href="/">Overview</Link><Link className="whitespace-nowrap rounded px-3 py-2 text-sm font-medium text-text-secondary hover:bg-surface-container-high" href="/exceptions">Reconciliation</Link><Link className="whitespace-nowrap rounded px-3 py-2 text-sm font-medium text-text-secondary hover:bg-surface-container-high" href="/settlements">Settlements</Link></nav></div></header><div className="mx-auto max-w-[1200px] px-4 py-8 sm:px-6 lg:px-8"><div className="mb-8 flex flex-col justify-between gap-4 border-b border-border-subtle pb-6 sm:flex-row sm:items-end"><div><p className="font-mono text-xs uppercase tracking-[0.14em] text-secondary">Transaction investigation</p><h1 className="mt-2 font-display text-headline-xl">Financial chain</h1><p className="mt-2 text-sm text-text-secondary">Follow this payment from order through bank credit.</p></div><Link className="text-sm font-semibold text-secondary hover:underline" href="/exceptions">Back to exceptions</Link></div>{loading ? <div className="rounded-lg border border-border-subtle bg-surface-card p-10 text-center text-text-secondary">Loading transaction chain...</div> : error ? <div className="rounded-lg border border-status-critical-border bg-status-critical-bg p-6" role="alert"><h2 className="font-display text-headline-sm text-status-critical">Transaction chain unavailable</h2><p className="mt-2 text-sm text-text-secondary">{error}</p><button className="mt-4 rounded bg-primary px-4 py-2 text-sm font-semibold text-on-primary" onClick={() => window.location.reload()} type="button">Try again</button></div> : !chain ? <div className="rounded-lg border border-border-subtle bg-surface-card p-8 text-center text-text-secondary">No transaction chain was returned.</div> : <><div className="mb-5 rounded-lg border border-border-subtle bg-surface-card p-5 shadow-sm"><div className="flex flex-wrap items-center justify-between gap-3"><div><p className="font-mono text-[11px] uppercase tracking-[0.12em] text-text-muted">Payment reference</p><p className="mt-1 font-mono text-sm font-semibold">{chain.payment.id}</p></div><div className="flex flex-wrap gap-2"><span className="rounded bg-surface-subtle px-2 py-1 font-mono text-[11px] text-text-secondary">Payment: {label(chain.payment.status)}</span><span className="rounded bg-status-warning-bg px-2 py-1 font-mono text-[11px] font-semibold text-status-warning">Recon: {label(chain.payment.reconciliation_status)}</span></div></div>{chain.payment.created_at && <p className="mt-3 text-xs text-text-muted">Created {formatDateTime(chain.payment.created_at)}</p>}</div><div className="grid gap-4 lg:grid-cols-5">{[<ChainStage key="order" title="Order" state={stateFor("order", chain)}><p className="font-mono text-xs text-text-primary">{chain.order.id}</p><p className="mt-2 font-display text-financial-metric-md text-text-primary">{amount(chain.order.amount)}</p><p className="mt-1">Status: {label(chain.order.status)}</p></ChainStage>, <ChainStage key="payment" title="Payment" state={stateFor("payment", chain)}><p className="font-mono text-xs text-text-primary">{chain.payment.id}</p><p className="mt-2 font-display text-financial-metric-md text-text-primary">{amount(chain.payment.amount)}</p><p className="mt-1">Status: {label(chain.payment.status)}</p></ChainStage>, <ChainStage key="adjustment" title="Fee / Refund" state={stateFor("adjustment", chain)}><p>Fees: <strong className="text-text-primary">{amount(chain.fees)}</strong></p><p className="mt-2">Refunds: <strong className="text-text-primary">{chain.refunds.length}</strong></p>{chain.refunds.map((refund) => <p className="mt-2 font-mono text-xs" key={refund.id}>{refund.id}: {amount(refund.amount)} ({label(refund.status)})</p>)}</ChainStage>, <ChainStage key="settlement" title="Settlement" state={stateFor("settlement", chain)}>{chain.settlements.length === 0 ? <p>No settlement returned for this payment.</p> : chain.settlements.map((settlement) => <div className="mb-3 last:mb-0" key={settlement.id}><p className="font-mono text-xs text-text-primary">{settlement.id}</p><p className="mt-2 font-display text-financial-metric-md text-text-primary">{amount(settlement.amount)}</p><p className="mt-1">{label(settlement.status)} · expected {settlement.expected_date ? formatDate(settlement.expected_date) : "date unavailable"}</p></div>)}</ChainStage>, <ChainStage key="bank" title="Bank credit" state={stateFor("bank", chain)}>{chain.bank_transactions.length === 0 ? <p>No bank credit returned for this chain.</p> : chain.bank_transactions.map((transaction) => <div className="mb-3 last:mb-0" key={transaction.id}><p className="font-mono text-xs text-text-primary">{transaction.id}</p><p className="mt-2 font-display text-financial-metric-md text-text-primary">{amount(transaction.amount)}</p><p className="mt-1">{transaction.credited_date ? `Credited ${formatDate(transaction.credited_date)}` : "Credit date unavailable"}</p></div>)}</ChainStage>]}</div><p className="mt-6 text-xs text-text-muted">The highlighted stage reflects only statuses and records returned by the reconciliation API.</p></>}</div></main>;
}