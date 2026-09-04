"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { getTransactions, type TransactionRecord } from "@/lib/api";
import { formatDateTime, formatINR } from "@/lib/utils";

function label(value: string): string {
  return value.replaceAll("_", " ").replace(/\b\w/g, (character) => character.toUpperCase());
}

function statusClass(status: string): string {
  if (["settled", "matched"].includes(status)) return "bg-status-success-bg text-status-success";
  if (["missing", "delayed", "held", "bank_mismatch"].includes(status)) return "bg-status-critical-bg text-status-critical";
  return "bg-status-warning-bg text-status-warning";
}

export default function TransactionsPage() {
  const [transactions, setTransactions] = useState<TransactionRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    getTransactions(controller.signal)
      .then(setTransactions)
      .catch((requestError: unknown) => {
        if (!controller.signal.aborted) setError(requestError instanceof Error ? requestError.message : "Unable to load transactions.");
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, []);

  return <main className="min-h-screen bg-background text-text-primary"><header className="border-b border-border-subtle bg-surface-card"><div className="mx-auto flex max-w-[1440px] flex-col gap-4 px-4 py-4 sm:px-6 lg:flex-row lg:items-center lg:justify-between lg:px-8"><div><div className="flex items-center gap-2"><span className="font-display text-xl font-bold tracking-tight">ReconAI</span><span className="rounded bg-surface-subtle px-2 py-1 font-mono text-[10px] text-text-secondary">B2B</span></div><p className="mt-1 flex items-center gap-2 font-mono text-[11px] text-text-muted"><span className="h-1.5 w-1.5 rounded-full bg-status-success" />Razorpay connected</p></div><nav aria-label="Primary" className="flex max-w-full gap-1 overflow-x-auto rounded-lg bg-surface-container-low p-1"><Link className="whitespace-nowrap rounded px-3 py-2 text-sm font-medium text-text-secondary hover:bg-surface-container-high" href="/">Overview</Link><Link className="whitespace-nowrap rounded px-3 py-2 text-sm font-medium text-text-secondary hover:bg-surface-container-high" href="/exceptions">Reconciliation</Link><Link className="whitespace-nowrap rounded px-3 py-2 text-sm font-medium text-text-secondary hover:bg-surface-container-high" href="/settlements">Settlements</Link><Link className="whitespace-nowrap rounded bg-primary-container px-3 py-2 text-sm font-medium text-on-primary" href="/transactions">Transactions</Link><Link className="whitespace-nowrap rounded px-3 py-2 text-sm font-medium text-text-secondary hover:bg-surface-container-high" href="/copilot">AI Copilot</Link></nav></div></header><div className="mx-auto max-w-[1440px] px-4 py-8 sm:px-6 lg:px-8"><div className="mb-8 flex flex-col justify-between gap-4 border-b border-border-subtle pb-6 sm:flex-row sm:items-end"><div><p className="font-mono text-xs uppercase tracking-[0.14em] text-secondary">Payment ledger</p><h1 className="mt-2 font-display text-headline-xl">Transactions</h1><p className="mt-2 text-sm text-text-secondary">Inspect payments and follow each one through its financial chain.</p></div><Link className="text-sm font-semibold text-secondary hover:underline" href="/">Back to overview</Link></div>{loading ? <div className="rounded-lg border border-border-subtle bg-surface-card p-10 text-center text-text-secondary">Loading transactions...</div> : error ? <div className="rounded-lg border border-status-critical-border bg-status-critical-bg p-6" role="alert"><h2 className="font-display text-headline-sm text-status-critical">Transactions unavailable</h2><p className="mt-2 text-sm text-text-secondary">{error}</p><button className="mt-4 rounded bg-primary px-4 py-2 text-sm font-semibold text-on-primary" onClick={() => window.location.reload()} type="button">Try again</button></div> : transactions.length === 0 ? <div className="rounded-lg border border-status-success-border bg-status-success-bg p-8 text-center"><h2 className="font-display text-headline-sm text-status-success">No transactions found</h2><p className="mt-2 text-sm text-text-secondary">The backend returned no payment records.</p></div> : <div className="overflow-hidden rounded-lg border border-border-subtle bg-surface-card shadow-sm"><div className="overflow-x-auto"><table className="w-full min-w-[820px] border-collapse text-left"><thead className="bg-surface-subtle"><tr className="font-mono text-[11px] uppercase tracking-[0.1em] text-text-muted"><th className="px-5 py-3 font-medium">Payment</th><th className="px-5 py-3 font-medium">Amount</th><th className="px-5 py-3 font-medium">Payment status</th><th className="px-5 py-3 font-medium">Reconciliation</th><th className="px-5 py-3 font-medium">Created</th><th className="px-5 py-3 text-right font-medium">Action</th></tr></thead><tbody className="divide-y divide-border-subtle">{transactions.map((transaction) => <tr className="hover:bg-surface-subtle/60" key={transaction.id}><td className="px-5 py-4 font-mono text-xs font-semibold">{transaction.razorpay_payment_id}</td><td className="px-5 py-4 font-mono text-sm font-semibold">{formatINR(Number(transaction.amount))}</td><td className="px-5 py-4 text-sm">{label(transaction.status)}</td><td className="px-5 py-4"><span className={`rounded px-2 py-1 font-mono text-[11px] font-semibold uppercase ${statusClass(transaction.reconciliation_status)}`}>{label(transaction.reconciliation_status)}</span></td><td className="px-5 py-4 whitespace-nowrap text-sm text-text-secondary">{formatDateTime(transaction.created_at)}</td><td className="px-5 py-4 text-right"><Link className="text-sm font-semibold text-secondary hover:underline" href={`/transactions/${transaction.razorpay_payment_id}/chain`}>View chain</Link></td></tr>)}</tbody></table></div></div>}</div></main>;
}