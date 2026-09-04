"""Create Phase 1 financial reconciliation schema."""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20260904_0001"
down_revision = None
branch_labels = None
depends_on = None

MONEY = sa.Numeric(14, 2)


def enum_type(name: str, values: tuple[str, ...]) -> sa.Enum:
    return sa.Enum(
        *values,
        name=name,
        native_enum=False,
        create_constraint=True,
    )


def upgrade() -> None:
    op.create_table(
        "orders",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("razorpay_order_id", sa.String(length=64), nullable=False),
        sa.Column("amount", MONEY, nullable=False),
        sa.Column("currency", sa.String(length=3), server_default=sa.text("'INR'"), nullable=False),
        sa.Column(
            "status",
            enum_type("order_status", ("created", "attempted", "paid")),
            server_default="created",
            nullable=False,
        ),
        sa.Column("receipt", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("amount >= 0", name="ck_orders_amount_non_negative"),
        sa.CheckConstraint("char_length(currency) = 3", name="ck_orders_currency_code_length"),
        sa.UniqueConstraint("razorpay_order_id", name="uq_orders_razorpay_order_id"),
    )
    op.create_index("ix_orders_receipt", "orders", ["receipt"])
    op.create_index("ix_orders_status_created_at", "orders", ["status", "created_at"])

    op.create_table(
        "payments",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("razorpay_payment_id", sa.String(length=64), nullable=False),
        sa.Column("order_id", sa.BigInteger(), nullable=False),
        sa.Column("amount", MONEY, nullable=False),
        sa.Column("fee", MONEY, nullable=False),
        sa.Column("tax", MONEY, nullable=False),
        sa.Column(
            "status",
            enum_type(
                "payment_status", ("created", "authorized", "captured", "refunded", "failed")
            ),
            nullable=False,
        ),
        sa.Column("method", sa.String(length=32), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "reconciliation_status",
            enum_type(
                "payment_reconciliation_status",
                (
                    "pending",
                    "processing",
                    "delayed",
                    "settled",
                    "held",
                    "matched",
                    "fallback_matched",
                    "partially_matched",
                    "duplicate_flagged",
                    "missing",
                    "fee_mismatch",
                    "bank_mismatch",
                ),
            ),
            server_default="pending",
            nullable=False,
        ),
        sa.CheckConstraint("amount >= 0", name="ck_payments_amount_non_negative"),
        sa.CheckConstraint("fee >= 0", name="ck_payments_fee_non_negative"),
        sa.CheckConstraint("tax >= 0", name="ck_payments_tax_non_negative"),
        sa.ForeignKeyConstraint(
            ["order_id"], ["orders.id"], name="fk_payments_order_id", ondelete="RESTRICT"
        ),
        sa.UniqueConstraint("razorpay_payment_id", name="uq_payments_razorpay_payment_id"),
    )
    op.create_index("ix_payments_order_id", "payments", ["order_id"])
    op.create_index("ix_payments_reconciliation_status", "payments", ["reconciliation_status"])
    op.create_index("ix_payments_status_created_at", "payments", ["status", "created_at"])

    op.create_table(
        "refunds",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("razorpay_refund_id", sa.String(length=64), nullable=False),
        sa.Column("payment_id", sa.BigInteger(), nullable=False),
        sa.Column("amount", MONEY, nullable=False),
        sa.Column(
            "status",
            enum_type("refund_status", ("pending", "processed", "failed")),
            server_default="pending",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("amount >= 0", name="ck_refunds_amount_non_negative"),
        sa.ForeignKeyConstraint(
            ["payment_id"], ["payments.id"], name="fk_refunds_payment_id", ondelete="RESTRICT"
        ),
        sa.UniqueConstraint("razorpay_refund_id", name="uq_refunds_razorpay_refund_id"),
    )
    op.create_index("ix_refunds_payment_id", "refunds", ["payment_id"])
    op.create_index("ix_refunds_status_created_at", "refunds", ["status", "created_at"])

    op.create_table(
        "fees",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("payment_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "type",
            enum_type("fee_type", ("gateway_fee", "gst", "other")),
            nullable=False,
        ),
        sa.Column("amount", MONEY, nullable=False),
        sa.CheckConstraint("amount >= 0", name="ck_fees_amount_non_negative"),
        sa.ForeignKeyConstraint(
            ["payment_id"], ["payments.id"], name="fk_fees_payment_id", ondelete="RESTRICT"
        ),
        sa.UniqueConstraint("payment_id", "type", name="uq_fees_payment_id_type"),
    )
    op.create_index("ix_fees_payment_id_type", "fees", ["payment_id", "type"])

    op.create_table(
        "settlements",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("razorpay_settlement_id", sa.String(length=64), nullable=True),
        sa.Column("amount", MONEY, nullable=False),
        sa.Column(
            "status",
            enum_type("settlement_status", ("processed", "processing", "on_hold")),
            server_default="processing",
            nullable=False,
        ),
        sa.Column("expected_date", sa.Date(), nullable=False),
        sa.Column("processed_date", sa.Date(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("amount >= 0", name="ck_settlements_amount_non_negative"),
        sa.UniqueConstraint("razorpay_settlement_id", name="uq_settlements_razorpay_settlement_id"),
    )
    op.create_index("ix_settlements_expected_date", "settlements", ["expected_date"])
    op.create_index(
        "ix_settlements_status_expected_date", "settlements", ["status", "expected_date"]
    )

    op.create_table(
        "settlement_items",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("settlement_id", sa.BigInteger(), nullable=False),
        sa.Column("payment_id", sa.BigInteger(), nullable=True),
        sa.Column("refund_id", sa.BigInteger(), nullable=True),
        sa.Column("amount", MONEY, nullable=False),
        sa.Column(
            "entry_type",
            enum_type("settlement_item_entry_type", ("payment", "refund", "fee_deduction")),
            nullable=False,
        ),
        sa.CheckConstraint(
            """
            (
                entry_type = 'payment'
                AND payment_id IS NOT NULL
                AND refund_id IS NULL
            )
            OR (
                entry_type = 'refund'
                AND refund_id IS NOT NULL
                AND payment_id IS NULL
            )
            OR (
                entry_type = 'fee_deduction'
                AND payment_id IS NOT NULL
                AND refund_id IS NULL
            )
            """,
            name="ck_settlement_items_reference_matches_entry_type",
        ),
        sa.ForeignKeyConstraint(
            ["settlement_id"],
            ["settlements.id"],
            name="fk_settlement_items_settlement_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["payment_id"],
            ["payments.id"],
            name="fk_settlement_items_payment_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["refund_id"], ["refunds.id"], name="fk_settlement_items_refund_id", ondelete="RESTRICT"
        ),
    )
    op.create_index(
        "ix_settlement_items_payment_entry_type", "settlement_items", ["payment_id", "entry_type"]
    )
    op.create_index("ix_settlement_items_refund_id", "settlement_items", ["refund_id"])
    op.create_index(
        "ix_settlement_items_settlement_entry_type",
        "settlement_items",
        ["settlement_id", "entry_type"],
    )

    op.create_table(
        "bank_transactions",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("settlement_id", sa.BigInteger(), nullable=True),
        sa.Column("amount", MONEY, nullable=False),
        sa.Column("credited_date", sa.Date(), nullable=True),
        sa.Column("bank_reference", sa.String(length=128), nullable=False),
        sa.CheckConstraint("amount >= 0", name="ck_bank_transactions_amount_non_negative"),
        sa.ForeignKeyConstraint(
            ["settlement_id"],
            ["settlements.id"],
            name="fk_bank_transactions_settlement_id",
            ondelete="SET NULL",
        ),
        sa.UniqueConstraint("bank_reference", name="uq_bank_transactions_bank_reference"),
    )
    op.create_index("ix_bank_transactions_credited_date", "bank_transactions", ["credited_date"])
    op.create_index("ix_bank_transactions_settlement_id", "bank_transactions", ["settlement_id"])

    op.create_table(
        "reconciliation_exceptions",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column(
            "type",
            enum_type(
                "reconciliation_exception_type",
                (
                    "delayed_settlement",
                    "missing_settlement",
                    "partial_settlement",
                    "duplicate",
                    "fee_mismatch",
                    "bank_credit_mismatch",
                    "unusual_pattern",
                ),
            ),
            nullable=False,
        ),
        sa.Column(
            "severity",
            enum_type("reconciliation_exception_severity", ("critical", "warning", "info")),
            nullable=False,
        ),
        sa.Column("related_order_id", sa.BigInteger(), nullable=True),
        sa.Column("related_payment_id", sa.BigInteger(), nullable=True),
        sa.Column("related_settlement_id", sa.BigInteger(), nullable=True),
        sa.Column("expected_amount", MONEY, server_default="0", nullable=False),
        sa.Column("actual_amount", MONEY, server_default="0", nullable=False),
        sa.Column("discrepancy", MONEY, server_default="0", nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "status",
            enum_type("reconciliation_exception_status", ("open", "investigating", "resolved")),
            server_default="open",
            nullable=False,
        ),
        sa.Column(
            "detected_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "expected_amount >= 0", name="ck_reconciliation_exceptions_expected_amount_non_negative"
        ),
        sa.CheckConstraint(
            "actual_amount >= 0", name="ck_reconciliation_exceptions_actual_amount_non_negative"
        ),
        sa.CheckConstraint(
            "char_length(description) > 0", name="ck_reconciliation_exceptions_description_required"
        ),
        sa.ForeignKeyConstraint(
            ["related_order_id"],
            ["orders.id"],
            name="fk_reconciliation_exceptions_related_order_id",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["related_payment_id"],
            ["payments.id"],
            name="fk_reconciliation_exceptions_related_payment_id",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["related_settlement_id"],
            ["settlements.id"],
            name="fk_reconciliation_exceptions_related_settlement_id",
            ondelete="SET NULL",
        ),
    )
    op.create_index(
        "ix_reconciliation_exceptions_detected_at", "reconciliation_exceptions", ["detected_at"]
    )
    op.create_index(
        "ix_reconciliation_exceptions_payment_id",
        "reconciliation_exceptions",
        ["related_payment_id"],
    )
    op.create_index(
        "ix_reconciliation_exceptions_settlement_id",
        "reconciliation_exceptions",
        ["related_settlement_id"],
    )
    op.create_index(
        "ix_reconciliation_exceptions_type_status", "reconciliation_exceptions", ["type", "status"]
    )
    op.create_index(
        "ix_reconciliation_exceptions_severity_status",
        "reconciliation_exceptions",
        ["severity", "status"],
    )


def downgrade() -> None:
    op.drop_table("reconciliation_exceptions")
    op.drop_table("bank_transactions")
    op.drop_table("settlement_items")
    op.drop_table("settlements")
    op.drop_table("fees")
    op.drop_table("refunds")
    op.drop_table("payments")
    op.drop_table("orders")
