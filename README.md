# Razorpay Financial Intelligence

Razorpay Financial Intelligence is a merchant operations MVP for understanding the path from payment capture to settlement and bank credit. A deterministic FastAPI reconciliation engine establishes financial truth, while a Next.js operator interface exposes totals, exceptions, settlement health, transaction chains, and an AI investigation layer.

## 1. Overview

The system combines Razorpay Test API payment data with a deterministic synthetic settlement layer. It calculates expected, settled, and received amounts; detects reconciliation exceptions; and gives finance operators a focused workflow for answering where money is and what needs attention.

The AI Copilot is not the source of financial truth. It calls backend tools that use the same service-layer functions as the REST endpoints and explains the resulting records in natural language.

## 2. Problem

Merchant finance teams reconcile several related records rather than one ledger entry:

- captured payments and refunds
- gateway fees and tax components
- settlement batches and settlement items
- bank credits and UTR references
- expected dates, processing delays, and discrepancies

Manual reconciliation makes it difficult to identify whether a shortfall is a missing settlement, a partial or duplicate item, a fee mismatch, or a bank-credit problem. Investigating one issue also requires following the complete Order → Payment → Refund/Fee → Settlement → Bank Credit chain.

## 3. Solution

The implemented workflow is:

```text
Razorpay Test API payments/orders/refunds
                    │
                    ▼
          FastAPI seeder and SQLAlchemy
                    │
                    ▼
 PostgreSQL financial records and synthetic settlements
                    │
                    ▼
       deterministic reconciliation engine
                    │
                    ▼
   payment statuses and exception records
                    │
          ┌─────────┴─────────┐
          ▼                   ▼
   dashboard/operator UI   transaction investigation
                                  │
                                  ▼
                        backend-grounded Copilot
```

The seeder preserves Razorpay ingestion and fills a deterministic synthetic demo cohort when Test Mode has no usable payments. The reconciliation engine performs calculations and writes derived statuses and exceptions. The frontend reads those APIs; it does not calculate financial truth independently.

## 4. Key Features

### Reconciliation scenarios

The validated demo cohort exercises these six hard exception scenarios:

1. **Missing settlement**: `pay_miss_50k` has no settlement item after its expected date.
2. **Partial settlement**: the payment settlement item is less than the expected amount.
3. **Duplicate settlement**: multiple payment items reference the same payment.
4. **Fee mismatch**: the settlement fee deduction differs from the payment fee total.
5. **Delayed settlement**: a processing settlement is past its expected date.
6. **Bank-credit mismatch**: a processed settlement's bank credit differs from the settlement amount.

### Operator product

- Overview dashboard with expected, settled, received, pending variance, and active exception totals.
- Filterable Exceptions screen with severity badges and status updates.
- Settlement Intelligence screen with status, expected/processed dates, overdue days, and detail data.
- Transactions screen backed by `GET /api/transactions`.
- Transaction chain detail for Order → Payment → Fee/Refund → Settlement → Bank Credit.
- API loading, error, retry, and empty states across the frontend screens.
- Next.js proxy routing for browser-safe local communication with the FastAPI backend.
- AI Copilot chat UI with suggested questions, tool metadata, and source-reference links.

`unusual_pattern` appears in the enum/specification as a soft insight, but it is not implemented as a blocking detector in the current reconciliation engine.

## 5. Demo Dataset

When Razorpay Test Mode returns no usable payments, the deterministic fallback creates the validated demo scale:

| Entity | Fallback count |
|---|---:|
| Orders | 16 |
| Payments | 16 |
| Fee rows | 32 |
| Settlements | 15 |
| Settlement items | 31 |
| Bank transactions | 14 |
| Refunds | Depends on Razorpay data; empty fallback creates none |
| Open reconciliation exceptions after reconciliation | 6 |

The six exception types listed above are generated from realistic payment, fee, settlement-item, settlement, and bank-credit conditions. Synthetic identifiers use stable prefixes such as `pay_synth_*`, `synth_ord_*`, and `set_*`. The seeder uses a fixed random seed for generated settlement/reference values and avoids duplicate synthetic records on rerun.

If Razorpay returns usable payments, those records are ingested first and remain part of the resulting dataset. The fallback fills the synthetic demo cohort independently of Razorpay availability.

## 6. Architecture

See [docs/architecture.md](docs/architecture.md) for the system diagram and component boundaries.

At a high level:

- **Frontend**: Next.js App Router, React, TypeScript, Tailwind CSS.
- **Proxy**: Next.js rewrites route `/backend-api/*` to the local FastAPI backend on port 8009 by default.
- **Backend**: FastAPI routes call SQLAlchemy-backed service functions.
- **Database**: PostgreSQL accessed through SQLAlchemy and psycopg.
- **Ingestion**: Razorpay Test API is called by the seeder.
- **AI**: the backend calls Gemini through `google-genai`; the browser never calls Gemini directly.

## 7. Reconciliation Flow

See [docs/reconciliation-flow.md](docs/reconciliation-flow.md).

The engine resets derived payment statuses, evaluates payment settlement items and fees, then evaluates settlement processing and bank credits. It creates `reconciliation_exceptions` for the six hard anomaly cases. Running reconciliation is an idempotent recalculation, but it clears and recreates exception rows, so operator-updated exception statuses are not preserved across a new run.

## 8. AI Copilot Architecture

See [docs/ai-copilot.md](docs/ai-copilot.md).

The Copilot receives a natural-language question at `POST /api/copilot/ask`. The backend Gemini agent can call five read-only tools:

- `query_transactions`
- `get_exceptions`
- `get_settlement_status`
- `compare_periods`
- `trace_transaction_chain`

The response contract is `{ answer, tool_calls_made, referenced_ids }`. The model is configured as `gemini-3.6-flash`, using `google-genai>=1.75,<2.0` for current function-call metadata support.

**AI Copilot is an investigation layer currently under validation.** The latest live verification reached Gemini but received a provider-side `503 UNAVAILABLE` high-demand response. No mock response or frontend fallback is used.

## 9. Database Model

See [docs/database-erd.md](docs/database-erd.md) for the Mermaid ER diagram. The eight application tables are:

- `orders`
- `payments`
- `refunds`
- `fees`
- `settlements`
- `settlement_items`
- `bank_transactions`
- `reconciliation_exceptions`

Foreign keys and delete behavior are defined in `backend/app/models/entities.py` and created by the initial Alembic migration.

## 10. Tech Stack

| Area | Technologies |
|---|---|
| Frontend | Next.js 15, React 19, TypeScript, Tailwind CSS |
| Backend | Python 3.11+, FastAPI, SQLAlchemy 2, Pydantic Settings |
| Database | PostgreSQL, psycopg, Alembic |
| External data | Razorpay Test API |
| AI | Gemini via `google-genai` 1.x |
| Testing | pytest, Node test runner, TypeScript compiler |
| Tooling | Uvicorn, Ruff, npm |

The MVP is intentionally single-tenant and local-development oriented. It does not include auth, Redis, Kafka, workers, RAG, vector databases, or production deployment infrastructure.

## 11. Project Structure

```text
.
├── PROJECT_SPEC.md
├── README.md
├── docs/
├── backend/
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   └── models/
│   ├── scripts/
│   ├── tests/
│   ├── pyproject.toml
│   └── alembic.ini
└── frontend/
    ├── src/app/
    │   ├── dashboard/
    │   ├── exceptions/
    │   ├── settlements/
    │   ├── transactions/
    │   └── copilot/
    ├── src/lib/
    ├── tests/
    └── package.json
```

## 12. API Endpoints

The FastAPI application is created in `backend/app/main.py`.

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Service and configuration health |
| GET | `/health/database` | Database connectivity check |
| POST | `/api/admin/seed` | Dev-only Razorpay ingestion and synthetic demo seeding |
| POST | `/api/admin/reconcile` | Dev-only reconciliation run |
| GET | `/api/dashboard/summary` | Date-scoped totals and top open exceptions |
| GET | `/api/transactions/` | Filterable payment list, maximum 50 records |
| GET | `/api/transactions/{payment_id}/chain` | Order-to-bank transaction chain |
| GET | `/api/exceptions/` | Exception list filtered by type, severity, and status |
| PATCH | `/api/exceptions/{exception_id}` | Update an exception status |
| GET | `/api/settlements/` | Settlement list filtered by status/date |
| GET | `/api/settlements/{settlement_id}` | Settlement items and bank transactions |
| POST | `/api/copilot/ask` | Backend Gemini investigation request |

The frontend uses a Next.js proxy in local development. The client default is `/backend-api`, which rewrites to `http://127.0.0.1:8009`; `NEXT_PUBLIC_API_BASE_URL` can override the client base path.

## 13. Local Setup

### Prerequisites

- Python 3.11 or newer
- Node.js and npm
- PostgreSQL running locally
- Razorpay Test Mode credentials for API-backed seeding
- Gemini API key for Copilot usage

### Environment

Copy `.env.example` to `.env` and fill values locally. Required variables are:

```text
DATABASE_URL=
RAZORPAY_KEY_ID=
RAZORPAY_KEY_SECRET=
GEMINI_API_KEY=
```

Never commit `.env`.

### Backend

```powershell
Set-Location backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
.\.venv\Scripts\alembic.exe upgrade head
.\.venv\Scripts\python.exe scripts\check_database.py
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8009
```

### Frontend

In a second terminal:

```powershell
Set-Location frontend
npm install
npm run dev -- --port 3000
```

The local frontend is available at `http://127.0.0.1:3000` unless another port is selected.

## 14. Demo Instructions

The following commands mutate the local development database and should be used only against the intended local PostgreSQL database:

```powershell
# With the backend running on port 8009:
Invoke-RestMethod -Uri "http://127.0.0.1:8009/api/admin/seed" -Method Post
Invoke-RestMethod -Uri "http://127.0.0.1:8009/api/admin/reconcile" -Method Post
```

Demo flow:

1. Open the dashboard and show expected, settled, received, and active exception totals.
2. Open Exceptions and show the six seeded anomaly types.
3. Open Settlements and show the delayed processing batch and overdue days.
4. Open Transactions and select `pay_miss_50k`.
5. Follow the chain to show the missing settlement break.
6. Optionally open Copilot and ask an investigation question if Gemini is available.
7. Close with the operating principle: deterministic reconciliation is financial truth; Gemini is the explanation/investigation layer.

## 15. Validation

The current repository has validated:

- Backend: 38 pytest tests passed.
- Frontend: 9 Node tests passed, including the transaction-list and proxy contracts.
- Frontend TypeScript typecheck passed.
- Frontend production build passed.
- Browser integration: dashboard, exceptions, settlements, transaction chain, Copilot route, and transaction list route loaded through the Next proxy.
- Live seeded API checks: 16 payments, 15 settlements, 14 bank transactions, and six open exception types were observed.

Copilot code and SDK compatibility tests pass, but live Gemini verification remains dependent on provider availability; the latest observed provider response was `503 UNAVAILABLE` due to temporary high demand.

## 16. Known Limitations

- **AI Copilot is currently under validation** because the configured Gemini provider returned a temporary `503 UNAVAILABLE` high-demand response during the latest live check.
- `unusual_pattern` is defined as a soft insight in the specification but is not implemented as a blocking reconciliation detector.
- Dashboard totals are date-scoped to the requested date, defaulting to today. A today-versus-yesterday delta is not currently returned by the dashboard API.
- Reconciliation clears and recreates exception rows on each run, so manually updated exception statuses are not preserved across a subsequent reconciliation run.
- The seeded synthetic dataset depends on Razorpay Test API access for real payment/refund ingestion when available; the deterministic fallback covers the demo when no usable payments are returned.
- Admin seed and reconcile endpoints are development endpoints and do not provide authentication in this MVP.
- Settlement and exception API behavior is implemented for the current frontend workflow; broader production hardening is out of scope.

## 17. Future Improvements

- Add provider-aware Copilot retries and operational observability.
- Add richer transaction search and filtering.
- Add more anomaly and trend insights without changing the deterministic source of truth.
- Improve production-grade ingestion, access control, and deployment hardening.

## License and submission notes

This repository is an MVP submission project. Local secrets belong in `.env`, which is ignored by Git; `.env.example` contains blank placeholders only.
