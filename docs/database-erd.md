# Database ER Diagram

The diagram below follows the SQLAlchemy entities and foreign keys in `backend/app/models/entities.py`. `settlement_items` can reference either a payment or a refund according to its `entry_type`; fee deductions reference a payment.

```mermaid
erDiagram
    ORDERS ||--o{ PAYMENTS : contains
    ORDERS ||--o{ RECONCILIATION_EXCEPTIONS : relates_to
    PAYMENTS ||--o{ REFUNDS : has
    PAYMENTS ||--o{ FEES : incurs
    PAYMENTS ||--o{ SETTLEMENT_ITEMS : appears_in
    PAYMENTS ||--o{ RECONCILIATION_EXCEPTIONS : relates_to
    REFUNDS ||--o{ SETTLEMENT_ITEMS : appears_in
    SETTLEMENTS ||--o{ SETTLEMENT_ITEMS : contains
    SETTLEMENTS ||--o{ BANK_TRANSACTIONS : credits
    SETTLEMENTS ||--o{ RECONCILIATION_EXCEPTIONS : relates_to

    ORDERS {
        bigint id PK
        string razorpay_order_id UK
        numeric amount
        string currency
        string status
        string receipt
        datetime created_at
    }

    PAYMENTS {
        bigint id PK
        string razorpay_payment_id UK
        bigint order_id FK
        numeric amount
        numeric fee
        numeric tax
        string status
        string method
        datetime created_at
        string reconciliation_status
    }

    REFUNDS {
        bigint id PK
        string razorpay_refund_id UK
        bigint payment_id FK
        numeric amount
        string status
        datetime created_at
    }

    FEES {
        bigint id PK
        bigint payment_id FK
        string type
        numeric amount
    }

    SETTLEMENTS {
        bigint id PK
        string razorpay_settlement_id UK
        numeric amount
        string status
        date expected_date
        date processed_date
        datetime created_at
    }

    SETTLEMENT_ITEMS {
        bigint id PK
        bigint settlement_id FK
        bigint payment_id FK
        bigint refund_id FK
        numeric amount
        string entry_type
    }

    BANK_TRANSACTIONS {
        bigint id PK
        bigint settlement_id FK
        numeric amount
        date credited_date
        string bank_reference UK
    }

    RECONCILIATION_EXCEPTIONS {
        bigint id PK
        string type
        string severity
        bigint related_order_id FK
        bigint related_payment_id FK
        bigint related_settlement_id FK
        numeric expected_amount
        numeric actual_amount
        numeric discrepancy
        string description
        string status
        datetime detected_at
    }
```

## Relationship notes

- Every payment requires an order through `payments.order_id`.
- Refunds and fees belong to payments.
- Settlement items belong to settlements and may reference a payment or refund.
- Bank transactions optionally belong to settlements; the foreign key uses `SET NULL` on settlement deletion.
- Exception references are nullable and use `SET NULL` on deletion.
- Entity-level uniqueness constraints cover Razorpay order/payment/refund/settlement identifiers, fee type per payment, and bank references.
