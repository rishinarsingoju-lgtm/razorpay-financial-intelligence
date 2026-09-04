from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.intelligence import get_settlement_status
from app.db.session import get_db
from app.models.entities import Settlement

router = APIRouter()


@router.get("/")
def list_settlements(
    status: str | None = Query(None),
    date_from: str | None = Query(None, description="ISO date, filters expected_date >="),
    date_to: str | None = Query(None, description="ISO date, filters expected_date <="),
    db: Session = Depends(get_db),
) -> Any:
    """
    Returns all settlements with optional status/date filters.
    Includes days-overdue for delayed batches so the frontend can render
    the overdue indicator.
    """
    from datetime import date as date_type, datetime

    stmt = select(Settlement)
    if status:
        from app.models.enums import SettlementStatus
        stmt = stmt.filter(Settlement.status == SettlementStatus(status))
    if date_from:
        stmt = stmt.filter(Settlement.expected_date >= datetime.fromisoformat(date_from).date())
    if date_to:
        stmt = stmt.filter(Settlement.expected_date <= datetime.fromisoformat(date_to).date())

    stmt = stmt.order_by(Settlement.expected_date.desc())
    settlements = db.execute(stmt).scalars().all()
    today = date_type.today()

    return [
        {
            "id": s.id,
            "razorpay_settlement_id": s.razorpay_settlement_id,
            "amount": float(s.amount),
            "status": s.status.value,
            "expected_date": s.expected_date.isoformat() if s.expected_date else None,
            "processed_date": s.processed_date.isoformat() if s.processed_date else None,
            "days_overdue": (
                (today - s.expected_date).days
                if s.expected_date and today > s.expected_date and s.status.value == "processing"
                else 0
            ),
            "item_count": len(s.items),
        }
        for s in settlements
    ]


@router.get("/{settlement_id}")
def get_settlement(
    settlement_id: int,
    db: Session = Depends(get_db),
) -> Any:
    """
    Returns full detail for a single settlement including its items and
    associated bank transactions.
    """
    s = db.execute(select(Settlement).filter_by(id=settlement_id)).scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="Settlement not found")

    return {
        "id": s.id,
        "razorpay_settlement_id": s.razorpay_settlement_id,
        "amount": float(s.amount),
        "status": s.status.value,
        "expected_date": s.expected_date.isoformat() if s.expected_date else None,
        "processed_date": s.processed_date.isoformat() if s.processed_date else None,
        "items": [
            {
                "id": si.id,
                "entry_type": si.entry_type.value,
                "amount": float(si.amount),
                "payment_id": si.payment.razorpay_payment_id if si.payment else None,
                "refund_id": si.refund.razorpay_refund_id if si.refund else None,
            }
            for si in s.items
        ],
        "bank_transactions": [
            {
                "id": bt.id,
                "amount": float(bt.amount),
                "credited_date": bt.credited_date.isoformat() if bt.credited_date else None,
                "bank_reference": bt.bank_reference,
            }
            for bt in s.bank_transactions
        ],
    }
