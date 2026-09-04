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

export type ExceptionRecord = {
  id: number;
  type: string;
  severity: "critical" | "warning" | "info" | string;
  status: "open" | "investigating" | "resolved" | string;
  expected_amount: number | string | null;
  actual_amount: number | string | null;
  discrepancy: number | string | null;
  description: string;
  detected_at: string;
  related_order_id: string | null;
  related_payment_id: string | null;
  related_settlement_id: string | null;
};

const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export async function getDashboardSummary(signal?: AbortSignal): Promise<DashboardSummary> {
  const response = await fetch(`${apiBaseUrl}/api/dashboard/summary`, { signal, cache: "no-store" });
  if (!response.ok) throw new Error(`Dashboard request failed (${response.status})`);
  return response.json() as Promise<DashboardSummary>;
}

export type ExceptionFilters = {
  type?: string;
  severity?: string;
  status?: string;
};

export async function getExceptions(filters: ExceptionFilters = {}, signal?: AbortSignal): Promise<ExceptionRecord[]> {
  const query = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value) query.set(key, value);
  });
  const queryString = query.toString();
  const response = await fetch(`${apiBaseUrl}/api/exceptions/${queryString ? `?${queryString}` : ""}`, {
    signal,
    cache: "no-store",
  });
  if (!response.ok) throw new Error(`Exceptions request failed (${response.status})`);
  return response.json() as Promise<ExceptionRecord[]>;
}

export async function updateExceptionStatus(exceptionId: number, status: string): Promise<void> {
  const response = await fetch(`${apiBaseUrl}/api/exceptions/${exceptionId}?status=${encodeURIComponent(status)}`, {
    method: "PATCH",
  });
  if (!response.ok) throw new Error(`Status update failed (${response.status})`);
}