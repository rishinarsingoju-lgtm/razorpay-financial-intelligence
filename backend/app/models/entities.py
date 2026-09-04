from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy import (
    Enum as SqlEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import (
    ExceptionSeverity,
    ExceptionStatus,
    ExceptionType,
    FeeType,
    OrderStatus,
    PaymentReconciliationStatus,
    PaymentStatus,
    RefundStatus,
    SettlementItemEntryType,
    SettlementStatus,
)

Money = Numeric(14, 2)


def enum_column(enum_class: type, name: str) -> SqlEnum:
    return SqlEnum(
        enum_class,
        name=name,
        values_callable=lambda values: [item.value for item in values],
        native_enum=False,
        create_constraint=True,
        validate_strings=True,
    )


class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (
        CheckConstraint("amount >= 0", name="ck_orders_amount_non_negative"),
        CheckConstraint("char_length(currency) = 3", name="ck_orders_currency_code_length"),
        UniqueConstraint("razorpay_order_id", name="uq_orders_razorpay_order_id"),
        Index("ix_orders_receipt", "receipt"),
        Index("ix_orders_status_created_at", "status", "created_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    razorpay_order_id: Mapped[str] = mapped_column(String(64), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Money, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, server_default="INR")
    status: Mapped[OrderStatus] = mapped_column(
        enum_column(OrderStatus, "order_status"),
        nullable=False,
        server_default=OrderStatus.CREATED.value,
    )
    receipt: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    payments: Mapped[list[Payment]] = relationship(back_populates="order")
    exceptions: Mapped[list[ReconciliationException]] = relationship(back_populates="related_order")


class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = (
        CheckConstraint("amount >= 0", name="ck_payments_amount_non_negative"),
        CheckConstraint("fee >= 0", name="ck_payments_fee_non_negative"),
        CheckConstraint("tax >= 0", name="ck_payments_tax_non_negative"),
        UniqueConstraint("razorpay_payment_id", name="uq_payments_razorpay_payment_id"),
        Index("ix_payments_order_id", "order_id"),
        Index("ix_payments_reconciliation_status", "reconciliation_status"),
        Index("ix_payments_status_created_at", "status", "created_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    razorpay_payment_id: Mapped[str] = mapped_column(String(64), nullable=False)
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", name="fk_payments_order_id", ondelete="RESTRICT"),
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(Money, nullable=False)
    fee: Mapped[Decimal] = mapped_column(Money, nullable=False)
    tax: Mapped[Decimal] = mapped_column(Money, nullable=False)
    status: Mapped[PaymentStatus] = mapped_column(
        enum_column(PaymentStatus, "payment_status"),
        nullable=False,
    )
    method: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    reconciliation_status: Mapped[PaymentReconciliationStatus] = mapped_column(
        enum_column(PaymentReconciliationStatus, "payment_reconciliation_status"),
        nullable=False,
        server_default=PaymentReconciliationStatus.PENDING.value,
    )

    order: Mapped[Order] = relationship(back_populates="payments")
    refunds: Mapped[list[Refund]] = relationship(back_populates="payment")
    fees: Mapped[list[Fee]] = relationship(back_populates="payment")
    settlement_items: Mapped[list[SettlementItem]] = relationship(back_populates="payment")
    exceptions: Mapped[list[ReconciliationException]] = relationship(
        back_populates="related_payment"
    )


class Refund(Base):
    __tablename__ = "refunds"
    __table_args__ = (
        CheckConstraint("amount >= 0", name="ck_refunds_amount_non_negative"),
        UniqueConstraint("razorpay_refund_id", name="uq_refunds_razorpay_refund_id"),
        Index("ix_refunds_payment_id", "payment_id"),
        Index("ix_refunds_status_created_at", "status", "created_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    razorpay_refund_id: Mapped[str] = mapped_column(String(64), nullable=False)
    payment_id: Mapped[int] = mapped_column(
        ForeignKey("payments.id", name="fk_refunds_payment_id", ondelete="RESTRICT"),
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(Money, nullable=False)
    status: Mapped[RefundStatus] = mapped_column(
        enum_column(RefundStatus, "refund_status"),
        nullable=False,
        server_default=RefundStatus.PENDING.value,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    payment: Mapped[Payment] = relationship(back_populates="refunds")
    settlement_items: Mapped[list[SettlementItem]] = relationship(back_populates="refund")


class Fee(Base):
    __tablename__ = "fees"
    __table_args__ = (
        CheckConstraint("amount >= 0", name="ck_fees_amount_non_negative"),
        UniqueConstraint("payment_id", "type", name="uq_fees_payment_id_type"),
        Index("ix_fees_payment_id_type", "payment_id", "type"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    payment_id: Mapped[int] = mapped_column(
        ForeignKey("payments.id", name="fk_fees_payment_id", ondelete="RESTRICT"),
        nullable=False,
    )
    type: Mapped[FeeType] = mapped_column(
        enum_column(FeeType, "fee_type"),
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(Money, nullable=False)

    payment: Mapped[Payment] = relationship(back_populates="fees")


class Settlement(Base):
    __tablename__ = "settlements"
    __table_args__ = (
        CheckConstraint("amount >= 0", name="ck_settlements_amount_non_negative"),
        UniqueConstraint("razorpay_settlement_id", name="uq_settlements_razorpay_settlement_id"),
        Index("ix_settlements_expected_date", "expected_date"),
        Index("ix_settlements_status_expected_date", "status", "expected_date"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    razorpay_settlement_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    amount: Mapped[Decimal] = mapped_column(Money, nullable=False)
    status: Mapped[SettlementStatus] = mapped_column(
        enum_column(SettlementStatus, "settlement_status"),
        nullable=False,
        server_default=SettlementStatus.PROCESSING.value,
    )
    expected_date: Mapped[date] = mapped_column(Date, nullable=False)
    processed_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    items: Mapped[list[SettlementItem]] = relationship(back_populates="settlement")
    bank_transactions: Mapped[list[BankTransaction]] = relationship(back_populates="settlement")
    exceptions: Mapped[list[ReconciliationException]] = relationship(
        back_populates="related_settlement"
    )


class SettlementItem(Base):
    __tablename__ = "settlement_items"
    __table_args__ = (
        CheckConstraint(
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
        Index("ix_settlement_items_payment_entry_type", "payment_id", "entry_type"),
        Index("ix_settlement_items_refund_id", "refund_id"),
        Index("ix_settlement_items_settlement_entry_type", "settlement_id", "entry_type"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    settlement_id: Mapped[int] = mapped_column(
        ForeignKey("settlements.id", name="fk_settlement_items_settlement_id", ondelete="RESTRICT"),
        nullable=False,
    )
    payment_id: Mapped[int | None] = mapped_column(
        ForeignKey("payments.id", name="fk_settlement_items_payment_id", ondelete="RESTRICT"),
        nullable=True,
    )
    refund_id: Mapped[int | None] = mapped_column(
        ForeignKey("refunds.id", name="fk_settlement_items_refund_id", ondelete="RESTRICT"),
        nullable=True,
    )
    amount: Mapped[Decimal] = mapped_column(Money, nullable=False)
    entry_type: Mapped[SettlementItemEntryType] = mapped_column(
        enum_column(SettlementItemEntryType, "settlement_item_entry_type"),
        nullable=False,
    )

    settlement: Mapped[Settlement] = relationship(back_populates="items")
    payment: Mapped[Payment | None] = relationship(back_populates="settlement_items")
    refund: Mapped[Refund | None] = relationship(back_populates="settlement_items")


class BankTransaction(Base):
    __tablename__ = "bank_transactions"
    __table_args__ = (
        CheckConstraint("amount >= 0", name="ck_bank_transactions_amount_non_negative"),
        UniqueConstraint("bank_reference", name="uq_bank_transactions_bank_reference"),
        Index("ix_bank_transactions_credited_date", "credited_date"),
        Index("ix_bank_transactions_settlement_id", "settlement_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    settlement_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "settlements.id", name="fk_bank_transactions_settlement_id", ondelete="SET NULL"
        ),
        nullable=True,
    )
    amount: Mapped[Decimal] = mapped_column(Money, nullable=False)
    credited_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    bank_reference: Mapped[str] = mapped_column(String(128), nullable=False)

    settlement: Mapped[Settlement | None] = relationship(back_populates="bank_transactions")


class ReconciliationException(Base):
    __tablename__ = "reconciliation_exceptions"
    __table_args__ = (
        CheckConstraint(
            "expected_amount >= 0",
            name="ck_reconciliation_exceptions_expected_amount_non_negative",
        ),
        CheckConstraint(
            "actual_amount >= 0",
            name="ck_reconciliation_exceptions_actual_amount_non_negative",
        ),
        CheckConstraint(
            "char_length(description) > 0",
            name="ck_reconciliation_exceptions_description_required",
        ),
        Index("ix_reconciliation_exceptions_detected_at", "detected_at"),
        Index("ix_reconciliation_exceptions_payment_id", "related_payment_id"),
        Index("ix_reconciliation_exceptions_settlement_id", "related_settlement_id"),
        Index("ix_reconciliation_exceptions_type_status", "type", "status"),
        Index("ix_reconciliation_exceptions_severity_status", "severity", "status"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    type: Mapped[ExceptionType] = mapped_column(
        enum_column(ExceptionType, "reconciliation_exception_type"),
        nullable=False,
    )
    severity: Mapped[ExceptionSeverity] = mapped_column(
        enum_column(ExceptionSeverity, "reconciliation_exception_severity"),
        nullable=False,
    )
    related_order_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "orders.id", name="fk_reconciliation_exceptions_related_order_id", ondelete="SET NULL"
        ),
        nullable=True,
    )
    related_payment_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "payments.id",
            name="fk_reconciliation_exceptions_related_payment_id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    related_settlement_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "settlements.id",
            name="fk_reconciliation_exceptions_related_settlement_id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    expected_amount: Mapped[Decimal] = mapped_column(Money, nullable=False, server_default="0")
    actual_amount: Mapped[Decimal] = mapped_column(Money, nullable=False, server_default="0")
    discrepancy: Mapped[Decimal] = mapped_column(Money, nullable=False, server_default="0")
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[ExceptionStatus] = mapped_column(
        enum_column(ExceptionStatus, "reconciliation_exception_status"),
        nullable=False,
        server_default=ExceptionStatus.OPEN.value,
    )
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    related_order: Mapped[Order | None] = relationship(back_populates="exceptions")
    related_payment: Mapped[Payment | None] = relationship(back_populates="exceptions")
    related_settlement: Mapped[Settlement | None] = relationship(back_populates="exceptions")
