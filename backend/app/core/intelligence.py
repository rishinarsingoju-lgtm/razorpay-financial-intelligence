from __future__ import annotations

import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.entities import (
    BankTransaction,
    Fee,
    Order,
    Payment,
    ReconciliationException,
    Refund,
    Settlement,
    SettlementItem,
)
from app.models.enums import ExceptionStatus, PaymentStatus

logger = logging.getLogger(__name__)

def get_dashboard_summary(db: Session, target_date: date | None = None) -> dict[str, Any]:
    if not target_date:
        target_date = date.today()
        
    # Get exceptions count
    exceptions_count = db.execute(
        select(func.count(ReconciliationException.id))
        .filter(ReconciliationException.status != ExceptionStatus.RESOLVED)
    ).scalar_one()

    top_exceptions = db.execute(
        select(ReconciliationException)
        .filter(ReconciliationException.status != ExceptionStatus.RESOLVED)
        .order_by(ReconciliationException.detected_at.desc())
        .limit(3)
    ).scalars().all()

    def calc_totals(d: date) -> dict[str, Decimal]:
        # expected: payments captured on date - refunds on date - fees on date
        captured_payments = db.execute(
            select(func.sum(Payment.amount))
            .filter(Payment.status == PaymentStatus.CAPTURED, func.date(Payment.created_at) == d)
        ).scalar_one() or Decimal(0)
        
        refunds = db.execute(
            select(func.sum(Refund.amount))
            .filter(func.date(Refund.created_at) == d)
        ).scalar_one() or Decimal(0)
        
        # approximate fees via payment joins
        fees = db.execute(
            select(func.sum(Fee.amount))
            .join(Payment)
            .filter(func.date(Payment.created_at) == d)
        ).scalar_one() or Decimal(0)
        
        expected = captured_payments - refunds - fees

        settled = db.execute(
            select(func.sum(Settlement.amount))
            .filter(Settlement.expected_date == d)
        ).scalar_one() or Decimal(0)

        received = db.execute(
            select(func.sum(BankTransaction.amount))
            .filter(BankTransaction.credited_date == d)
        ).scalar_one() or Decimal(0)

        return {"expected": expected, "settled": settled, "received": received}

    today_totals = calc_totals(target_date)
    return {
        "totals": today_totals,
        "exception_count": exceptions_count,
        "top_exceptions": [
            {
                "id": exc.id,
                "type": exc.type.value,
                "severity": exc.severity.value,
                "description": exc.description,
            }
            for exc in top_exceptions
        ]
    }

def query_transactions(
    db: Session,
    amount_min: float | None = None,
    amount_max: float | None = None,
    status: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    unmatched_only: bool = False
) -> list[dict[str, Any]]:
    stmt = select(Payment)
    
    if amount_min is not None:
        stmt = stmt.filter(Payment.amount >= amount_min)
    if amount_max is not None:
        stmt = stmt.filter(Payment.amount <= amount_max)
    if status:
        stmt = stmt.filter(Payment.reconciliation_status == status)
    if date_from:
        stmt = stmt.filter(Payment.created_at >= datetime.fromisoformat(date_from))
    if date_to:
        stmt = stmt.filter(Payment.created_at <= datetime.fromisoformat(date_to))
    if unmatched_only:
        stmt = stmt.filter(Payment.reconciliation_status != "settled")
        
    payments = db.execute(stmt.limit(50)).scalars().all()
    return [
        {
            "id": p.id,
            "razorpay_payment_id": p.razorpay_payment_id,
            "amount": float(p.amount),
            "status": p.status.value,
            "reconciliation_status": p.reconciliation_status.value,
            "created_at": p.created_at.isoformat()
        }
        for p in payments
    ]

def trace_transaction_chain(db: Session, payment_id: str | None = None, order_id: str | None = None) -> dict[str, Any]:
    payment = None
    if payment_id:
        payment = db.execute(select(Payment).filter_by(razorpay_payment_id=payment_id)).scalar_one_or_none()
    elif order_id:
        order = db.execute(select(Order).filter_by(razorpay_order_id=order_id)).scalar_one_or_none()
        if order and order.payments:
            payment = order.payments[0]
            
    if not payment:
        return {"error": "Transaction not found"}
        
    chain = {
        "order": {
            "id": payment.order.razorpay_order_id,
            "amount": float(payment.order.amount),
            "status": payment.order.status.value
        },
        "payment": {
            "id": payment.razorpay_payment_id,
            "amount": float(payment.amount),
            "status": payment.status.value,
            "reconciliation_status": payment.reconciliation_status.value
        },
        "refunds": [
            {"id": r.razorpay_refund_id, "amount": float(r.amount), "status": r.status.value}
            for r in payment.refunds
        ],
        "fees": sum(float(f.amount) for f in payment.fees),
        "settlements": [],
        "bank_transactions": []
    }
    
    for si in payment.settlement_items:
        s = si.settlement
        chain["settlements"].append({
            "id": s.razorpay_settlement_id,
            "amount": float(s.amount),
            "status": s.status.value,
            "expected_date": s.expected_date.isoformat() if s.expected_date else None
        })
        for bt in s.bank_transactions:
            chain["bank_transactions"].append({
                "id": bt.bank_reference,
                "amount": float(bt.amount),
                "credited_date": bt.credited_date.isoformat() if bt.credited_date else None
            })
            
    return chain

def compare_periods(db: Session, period_a_start: str, period_a_end: str, period_b_start: str, period_b_end: str) -> dict[str, Any]:
    def get_period_data(start, end):
        dt_start = datetime.fromisoformat(start)
        dt_end = datetime.fromisoformat(end)
        
        captured_payments = db.execute(
            select(func.sum(Payment.amount))
            .filter(Payment.status == PaymentStatus.CAPTURED, Payment.created_at >= dt_start, Payment.created_at <= dt_end)
        ).scalar_one() or Decimal(0)
        
        refunds = db.execute(
            select(func.sum(Refund.amount))
            .filter(Refund.created_at >= dt_start, Refund.created_at <= dt_end)
        ).scalar_one() or Decimal(0)
        
        return {
            "captured_amount": float(captured_payments),
            "refunded_amount": float(refunds),
            "net_amount": float(captured_payments - refunds)
        }
        
    return {
        "period_a": get_period_data(period_a_start, period_a_end),
        "period_b": get_period_data(period_b_start, period_b_end)
    }

def get_exceptions_info(
    db: Session,
    type: str | None = None,
    severity: str | None = None,
    status: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None
) -> list[dict[str, Any]]:
    stmt = select(ReconciliationException)
    
    if type:
        stmt = stmt.filter(ReconciliationException.type == type)
    if severity:
        stmt = stmt.filter(ReconciliationException.severity == severity)
    if status:
        stmt = stmt.filter(ReconciliationException.status == status)
    if date_from:
        stmt = stmt.filter(ReconciliationException.detected_at >= datetime.fromisoformat(date_from))
    if date_to:
        stmt = stmt.filter(ReconciliationException.detected_at <= datetime.fromisoformat(date_to))
        
    exceptions = db.execute(stmt.limit(50)).scalars().all()
    return [
        {
            "id": exc.id,
            "type": exc.type.value,
            "severity": exc.severity.value,
            "status": exc.status.value,
            "discrepancy": float(exc.discrepancy),
            "description": exc.description,
            "related_payment_id": exc.related_payment.razorpay_payment_id if exc.related_payment else None
        }
        for exc in exceptions
    ]

def get_settlement_status(db: Session, settlement_id: str | None = None, date_range: str | None = None) -> list[dict[str, Any]]:
    stmt = select(Settlement)
    if settlement_id:
        stmt = stmt.filter(Settlement.razorpay_settlement_id == settlement_id)
        
    settlements = db.execute(stmt.limit(50)).scalars().all()
    return [
        {
            "id": s.razorpay_settlement_id,
            "amount": float(s.amount),
            "status": s.status.value,
            "expected_date": s.expected_date.isoformat() if s.expected_date else None,
            "processed_date": s.processed_date.isoformat() if s.processed_date else None
        }
        for s in settlements
    ]
