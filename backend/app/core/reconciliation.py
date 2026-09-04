from __future__ import annotations

import logging
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.entities import (
    BankTransaction,
    Fee,
    Payment,
    ReconciliationException,
    Refund,
    Settlement,
    SettlementItem,
)
from app.models.enums import (
    ExceptionSeverity,
    ExceptionStatus,
    ExceptionType,
    PaymentReconciliationStatus,
    SettlementItemEntryType,
    SettlementStatus,
)

logger = logging.getLogger(__name__)


def run_reconciliation(db: Session) -> dict:
    """
    Core reconciliation engine based on deterministic rules.
    Runs idempotently by clearing previous exceptions and resetting statuses.
    """
    stats = {
        "payments_processed": 0,
        "settlements_processed": 0,
        "exceptions_created": 0,
    }
    today = date.today()

    # 1. Idempotency: clear existing exceptions and reset payment statuses
    db.execute(delete(ReconciliationException))
    db.flush()

    payments = db.execute(select(Payment)).scalars().all()
    for p in payments:
        p.reconciliation_status = PaymentReconciliationStatus.PENDING
    db.flush()

    # 2. Process Payments
    for p in payments:
        stats["payments_processed"] += 1

        # Calculate expected amount
        refunds_total = sum(r.amount for r in p.refunds)
        fees_total = sum(f.amount for f in p.fees)
        expected_amount = p.amount - refunds_total - fees_total

        # Find settlement items
        payment_items = [si for si in p.settlement_items if si.entry_type == SettlementItemEntryType.PAYMENT]
        fee_items = [si for si in p.settlement_items if si.entry_type == SettlementItemEntryType.FEE_DEDUCTION]
        refund_items = [si for si in p.settlement_items if si.entry_type == SettlementItemEntryType.REFUND]

        # Calculate settled amount for this payment (signed sum of items related to payment)
        settled_amount = sum(si.amount for si in p.settlement_items)

        exception_created = False

        if not p.settlement_items:
            expected_date = p.created_at.date() + timedelta(days=2)
            if today > expected_date:
                exc = ReconciliationException(
                    type=ExceptionType.MISSING_SETTLEMENT,
                    severity=ExceptionSeverity.CRITICAL,
                    related_order_id=p.order_id,
                    related_payment_id=p.id,
                    expected_amount=expected_amount,
                    actual_amount=Decimal(0),
                    discrepancy=expected_amount,
                    description=f"Missing settlement for payment {p.razorpay_payment_id}. Expected by {expected_date}."
                )
                db.add(exc)
                p.reconciliation_status = PaymentReconciliationStatus.MISSING
                stats["exceptions_created"] += 1
                exception_created = True
        else:
            # Check for duplicate
            if len(payment_items) >= 2:
                actual_amount = sum(si.amount for si in payment_items)
                discrepancy = actual_amount - p.amount
                exc = ReconciliationException(
                    type=ExceptionType.DUPLICATE,
                    severity=ExceptionSeverity.CRITICAL,
                    related_order_id=p.order_id,
                    related_payment_id=p.id,
                    expected_amount=p.amount,
                    actual_amount=actual_amount,
                    discrepancy=discrepancy,
                    description=f"Duplicate settlement items found for payment {p.razorpay_payment_id}."
                )
                db.add(exc)
                p.reconciliation_status = PaymentReconciliationStatus.DUPLICATE_FLAGGED
                stats["exceptions_created"] += 1
                exception_created = True

            # Check for fee mismatch
            deducted_fees = sum(abs(si.amount) for si in fee_items)
            if deducted_fees != fees_total:
                discrepancy = abs(deducted_fees - fees_total)
                exc = ReconciliationException(
                    type=ExceptionType.FEE_MISMATCH,
                    severity=ExceptionSeverity.WARNING,
                    related_order_id=p.order_id,
                    related_payment_id=p.id,
                    expected_amount=fees_total,
                    actual_amount=deducted_fees,
                    discrepancy=discrepancy,
                    description=f"Fee mismatch for payment {p.razorpay_payment_id}. Expected: {fees_total}, Deducted: {deducted_fees}"
                )
                db.add(exc)
                if not exception_created:
                    p.reconciliation_status = PaymentReconciliationStatus.FEE_MISMATCH
                stats["exceptions_created"] += 1
                exception_created = True

            # Check for partial settlement
            if settled_amount < expected_amount and settled_amount > 0 and len(payment_items) < 2:
                discrepancy = expected_amount - settled_amount
                exc = ReconciliationException(
                    type=ExceptionType.PARTIAL_SETTLEMENT,
                    severity=ExceptionSeverity.WARNING,
                    related_order_id=p.order_id,
                    related_payment_id=p.id,
                    expected_amount=expected_amount,
                    actual_amount=settled_amount,
                    discrepancy=discrepancy,
                    description=f"Partial settlement for payment {p.razorpay_payment_id}. Expected: {expected_amount}, Settled: {settled_amount}"
                )
                db.add(exc)
                if not exception_created:
                    p.reconciliation_status = PaymentReconciliationStatus.PARTIALLY_MATCHED
                stats["exceptions_created"] += 1
                exception_created = True

            # If no exception and not missing, determine matched state
            if not exception_created:
                # Get the settlement for the primary payment item
                primary_settlement = payment_items[0].settlement if payment_items else None
                if primary_settlement:
                    if primary_settlement.status == SettlementStatus.PROCESSED:
                        p.reconciliation_status = PaymentReconciliationStatus.SETTLED
                    elif primary_settlement.status == SettlementStatus.PROCESSING:
                        if today > primary_settlement.expected_date:
                            p.reconciliation_status = PaymentReconciliationStatus.DELAYED
                        else:
                            p.reconciliation_status = PaymentReconciliationStatus.PROCESSING
                    elif primary_settlement.status == SettlementStatus.ON_HOLD:
                        p.reconciliation_status = PaymentReconciliationStatus.HELD
                else:
                    p.reconciliation_status = PaymentReconciliationStatus.MATCHED
                    
    db.flush()

    # 3. Process Settlements
    settlements = db.execute(select(Settlement)).scalars().all()
    for s in settlements:
        stats["settlements_processed"] += 1
        
        # Delayed Settlement
        if s.status == SettlementStatus.PROCESSING and today > s.expected_date:
            exc = ReconciliationException(
                type=ExceptionType.DELAYED_SETTLEMENT,
                severity=ExceptionSeverity.WARNING,
                related_settlement_id=s.id,
                expected_amount=s.amount,
                actual_amount=Decimal(0),
                discrepancy=s.amount,
                description=f"Settlement {s.razorpay_settlement_id} is delayed. Expected on {s.expected_date}."
            )
            db.add(exc)
            stats["exceptions_created"] += 1
            
        # Bank Credit Mismatch
        if s.status == SettlementStatus.PROCESSED:
            bank_received = sum(bt.amount for bt in s.bank_transactions if bt.credited_date is not None)
            if bank_received != s.amount:
                discrepancy = abs(s.amount - bank_received)
                exc = ReconciliationException(
                    type=ExceptionType.BANK_CREDIT_MISMATCH,
                    severity=ExceptionSeverity.CRITICAL,
                    related_settlement_id=s.id,
                    expected_amount=s.amount,
                    actual_amount=bank_received,
                    discrepancy=discrepancy,
                    description=f"Bank credit mismatch for settlement {s.razorpay_settlement_id}. Expected: {s.amount}, Received: {bank_received}"
                )
                db.add(exc)
                stats["exceptions_created"] += 1
                
                # Update payment statuses to reflect bank mismatch if they were SETTLED
                for si in s.items:
                    if si.payment and si.payment.reconciliation_status == PaymentReconciliationStatus.SETTLED:
                        si.payment.reconciliation_status = PaymentReconciliationStatus.BANK_MISMATCH

    db.commit()
    return stats
