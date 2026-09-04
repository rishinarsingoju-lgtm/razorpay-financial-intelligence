"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";

import { askCopilot, type CopilotResponse } from "@/lib/api";

type Message = { id: number; role: "user" | "assistant"; text: string; response?: CopilotResponse };

const navigation = [
  { label: "Overview", href: "/" },
  { label: "Reconciliation", href: "/exceptions" },
  { label: "Settlements", href: "/settlements" },
  { label: "Transactions", href: "/transactions" },
  { label: "AI Copilot", href: "/copilot" },
];

const suggestedQuestions = [
  "Why is today's settlement lower than yesterday?",
  "Where is the missing money?",
  "What exceptions need my attention?",
  "Explain this settlement batch's status.",
];

function sourceLink(id: string): { href: string; label: string } | null {
  if (id.startsWith("pay_")) return { href: `/transactions/${id}/chain`, label: `Payment ${id}` };
  if (id.startsWith("set_")) return { href: "/settlements", label: `Settlement ${id}` };
  return null;
}

export default function CopilotPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submitQuestion(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmedQuestion = question.trim();
    if (!trimmedQuestion || loading) return;
    const userMessage: Message = { id: Date.now(), role: "user", text: trimmedQuestion };
    setMessages((current) => [...current, userMessage]);
    setQuestion("");
    setError(null);
    setLoading(true);
    try {
      const response = await askCopilot(trimmedQuestion);
      setMessages((current) => [...current, { id: Date.now() + 1, role: "assistant", text: response.answer, response }]);
    } catch (requestError: unknown) {
      setError(requestError instanceof Error ? requestError.message : "Unable to reach AI Copilot.");
    } finally {
      setLoading(false);
    }
  }

  return <main className="min-h-screen bg-background text-text-primary"><header className="border-b border-border-subtle bg-surface-card"><div className="mx-auto flex max-w-[1440px] flex-col gap-4 px-4 py-4 sm:px-6 lg:flex-row lg:items-center lg:justify-between lg:px-8"><div><div className="flex items-center gap-2"><span className="font-display text-xl font-bold tracking-tight">ReconAI</span><span className="rounded bg-surface-subtle px-2 py-1 font-mono text-[10px] text-text-secondary">B2B</span></div><p className="mt-1 flex items-center gap-2 font-mono text-[11px] text-text-muted"><span className="h-1.5 w-1.5 rounded-full bg-status-success" />Razorpay connected</p></div><nav aria-label="Primary" className="flex max-w-full gap-1 overflow-x-auto rounded-lg bg-surface-container-low p-1">{navigation.map((item, index) => <Link className={`whitespace-nowrap rounded px-3 py-2 text-sm font-medium ${index === 4 ? "bg-primary-container text-on-primary" : "text-text-secondary hover:bg-surface-container-high"}`} href={item.href} key={item.href}>{item.label}</Link>)}</nav></div></header><div className="mx-auto max-w-[1000px] px-4 py-8 sm:px-6 lg:px-8"><div className="mb-8 border-b border-border-subtle pb-6"><p className="font-mono text-xs uppercase tracking-[0.14em] text-secondary">Read-only financial intelligence</p><h1 className="mt-2 font-display text-headline-xl">AI Copilot</h1><p className="mt-2 text-sm text-text-secondary">Ask questions about your payments, exceptions, and settlement flow. Answers are grounded in backend ledger data.</p></div><section className="rounded-lg border border-border-subtle bg-surface-card shadow-sm"><div className="flex items-center gap-3 border-b border-border-subtle p-5"><span className="flex h-9 w-9 items-center justify-center rounded-lg bg-secondary-fixed text-secondary">AI</span><div><h2 className="font-display text-headline-sm">Financial operations assistant</h2><p className="text-xs text-text-muted">Uses read-only reconciliation tools</p></div></div><div className="min-h-[320px] space-y-5 p-5 sm:p-8">{messages.length === 0 && <div className="mx-auto max-w-xl py-8 text-center"><p className="font-display text-headline-md">What would you like to investigate?</p><p className="mt-2 text-sm text-text-secondary">Choose a starting question or ask about a specific record.</p><div className="mt-6 flex flex-wrap justify-center gap-2">{suggestedQuestions.map((suggestion) => <button className="rounded border border-border-strong bg-surface-card px-3 py-2 text-left text-sm text-text-secondary hover:bg-surface-subtle" key={suggestion} onClick={() => setQuestion(suggestion)} type="button">{suggestion}</button>)}</div></div>}{messages.map((message) => <div className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`} key={message.id}><div className={`max-w-3xl rounded-lg px-4 py-3 ${message.role === "user" ? "bg-primary-container text-on-primary" : "border border-border-subtle bg-surface-subtle"}`}><p className="whitespace-pre-wrap text-sm leading-6">{message.text}</p>{message.response && <div className="mt-4 border-t border-border-strong pt-3"><p className="font-mono text-[11px] uppercase tracking-[0.1em] text-text-muted">Sources</p><div className="mt-2 flex flex-wrap gap-2">{message.response.referenced_ids.length === 0 ? <span className="text-xs text-text-muted">No record references returned.</span> : message.response.referenced_ids.map((id) => { const link = sourceLink(id); return link ? <Link className="rounded bg-surface-card px-2 py-1 font-mono text-[11px] text-secondary hover:underline" href={link.href} key={id}>{link.label}</Link> : <span className="rounded bg-surface-card px-2 py-1 font-mono text-[11px] text-text-secondary" key={id}>{id}</span>; })}</div><p className="mt-3 font-mono text-[11px] uppercase tracking-[0.1em] text-text-muted">Tools used</p><div className="mt-2 flex flex-wrap gap-2">{message.response.tool_calls_made.length === 0 ? <span className="text-xs text-text-muted">No tools reported.</span> : message.response.tool_calls_made.map((call, index) => <span className="rounded bg-surface-card px-2 py-1 font-mono text-[11px] text-text-secondary" key={`${call.tool}-${index}`}>{call.tool}</span>)}</div></div>}</div></div>)}{loading && <div className="flex justify-start"><div className="rounded-lg border border-secondary-fixed bg-secondary-fixed px-4 py-3 text-sm text-text-secondary"><span className="font-semibold text-secondary">Copilot is investigating</span><span className="ml-2 animate-pulse">Running read-only reconciliation tools...</span></div></div>}</div>{error && <div className="mx-5 mb-4 rounded border border-status-critical-border bg-status-critical-bg p-3 text-sm text-status-critical" role="alert"><div className="flex flex-wrap items-center justify-between gap-3"><span>{error}</span><button className="rounded bg-primary px-3 py-2 font-semibold text-on-primary" onClick={() => setError(null)} type="button">Dismiss</button></div></div>}<form className="border-t border-border-subtle p-4 sm:p-5" onSubmit={submitQuestion}><label className="sr-only" htmlFor="copilot-question">Ask AI Copilot</label><div className="flex flex-col gap-3 sm:flex-row"><input className="min-h-11 flex-1 rounded border border-border-strong bg-surface-card px-3 py-2 text-sm text-text-primary outline-none focus:border-secondary" id="copilot-question" onChange={(event) => setQuestion(event.target.value)} placeholder="Ask where your money is..." value={question} /><button className="rounded bg-primary px-5 py-2 text-sm font-semibold text-on-primary disabled:cursor-not-allowed disabled:opacity-50" disabled={loading || !question.trim()} type="submit">{loading ? "Investigating..." : "Ask Copilot"}</button></div><p className="mt-2 text-xs text-text-muted">Responses use the backend financial intelligence tools and may take a moment.</p></form></section></div></main>;
}