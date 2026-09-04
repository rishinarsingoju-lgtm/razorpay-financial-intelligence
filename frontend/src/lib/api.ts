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

export type SettlementRecord = {
  id: number;
  razorpay_settlement_id: string;
  amount: number | string;
  status: "processed" | "processing" | "on_hold" | string;
  expected_date: string | null;
  processed_date: string | null;
  days_overdue: number;
  item_count: number;
};

export type SettlementItem = {
  id: number;
  entry_type: string;
  amount: number | string;
  payment_id: string | null;
  refund_id: string | null;
};

export type SettlementBankTransaction = {
  id: number;
  amount: number | string;
  credited_date: string | null;
  bank_reference: string;
};

export type SettlementDetail = SettlementRecord & {
  items: SettlementItem[];
  bank_transactions: SettlementBankTransaction[];
};

export type TransactionChain = {
  order: { id: string; amount: number | string; status: string };
  payment: {
    id: string;
    amount: number | string;
    status: string;
    reconciliation_status: string;
    created_at?: string;
  };
  refunds: Array<{ id: string; amount: number | string; status: string }>;
  fees: number | string;
  settlements: Array<{ id: string; amount: number | string; status: string; expected_date: string | null }>;
  bank_transactions: Array<{ id: string; amount: number | string; credited_date: string | null }>;
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

export type SettlementFilters = {
  status?: string;
  date_from?: string;
  date_to?: string;
};

export async function getSettlements(filters: SettlementFilters = {}, signal?: AbortSignal): Promise<SettlementRecord[]> {
  const query = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value) query.set(key, value);
  });
  const queryString = query.toString();
  const response = await fetch(`${apiBaseUrl}/api/settlements/${queryString ? `?${queryString}` : ""}`, {
    signal,
    cache: "no-store",
  });
  if (!response.ok) throw new Error(`Settlements request failed (${response.status})`);
  return response.json() as Promise<SettlementRecord[]>;
}

export async function getSettlementDetail(settlementId: number, signal?: AbortSignal): Promise<SettlementDetail> {
  const response = await fetch(`${apiBaseUrl}/api/settlements/${settlementId}`, { signal, cache: "no-store" });
  if (!response.ok) throw new Error(`Settlement detail request failed (${response.status})`);
  return response.json() as Promise<SettlementDetail>;
}

export async function getTransactionChain(paymentId: string, signal?: AbortSignal): Promise<TransactionChain> {
  const response = await fetch(`${apiBaseUrl}/api/transactions/${encodeURIComponent(paymentId)}/chain`, {
    signal,
    cache: "no-store",
  });
  if (!response.ok) throw new Error(`Transaction chain request failed (${response.status})`);
  const payload = await response.json() as TransactionChain | { error: string };
  if ("error" in payload) throw new Error(payload.error);
  return payload;
}