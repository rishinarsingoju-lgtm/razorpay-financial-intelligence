export type DashboardException = {
  id: number;
  type: string;
  severity: string;
  description: string;
};

export type DashboardSummary = {
  totals: { expected: number; settled: number; received: number };
  exception_count: number;
  top_exceptions: DashboardException[];
};

const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export async function getDashboardSummary(signal?: AbortSignal): Promise<DashboardSummary> {
  const response = await fetch(`${apiBaseUrl}/api/dashboard/summary`, { signal, cache: "no-store" });
  if (!response.ok) throw new Error(`Dashboard request failed (${response.status})`);
  return response.json() as Promise<DashboardSummary>;
}