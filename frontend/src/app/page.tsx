const checks = [
  ["Backend", "FastAPI health endpoint ready"],
  ["Database", "SQLAlchemy models and Alembic migration ready"],
  ["Frontend", "Next.js TypeScript shell ready"],
];

export default function Home() {
  return (
    <main className="min-h-screen bg-background px-6 py-8 text-text-primary">
      <section className="mx-auto flex w-full max-w-5xl flex-col gap-6">
        <div className="flex items-center justify-between border-b border-border-subtle pb-4">
          <div>
            <p className="font-mono text-xs font-medium uppercase tracking-[0.12em] text-text-muted">
              Phase 1
            </p>
            <h1 className="font-display text-2xl font-semibold">Financial Intelligence Foundation</h1>
          </div>
          <span className="rounded bg-surface-subtle px-3 py-1 font-mono text-xs text-text-secondary">
            Local MVP
          </span>
        </div>

        <div className="grid gap-3 md:grid-cols-3">
          {checks.map(([label, value]) => (
            <div key={label} className="rounded-lg border border-border-subtle bg-surface p-4">
              <div className="font-mono text-xs uppercase text-text-muted">{label}</div>
              <div className="mt-2 text-sm font-medium">{value}</div>
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}
