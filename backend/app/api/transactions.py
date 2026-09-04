from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.intelligence import query_transactions, trace_transaction_chain
from app.db.session import get_db

router = APIRouter()


@router.get("/")
def list_transactions(
    amount_min: float | None = Query(None),
    amount_max: float | None = Query(None),
    status: str | None = Query(None),
    date_from: str | None = Query(None, description="ISO datetime"),
    date_to: str | None = Query(None, description="ISO datetime"),
    unmatched_only: bool = Query(False),
    db: Session = Depends(get_db),
) -> Any:
    """
    Returns a filtered list of payments (max 50).

    Query params mirror the agent tool signature so the same service function
    is called from both the REST layer and the AI tool layer.
    """
    return query_transactions(
        db=db,
        amount_min=amount_min,
        amount_max=amount_max,
        status=status,
        date_from=date_from,
        date_to=date_to,
        unmatched_only=unmatched_only,
    )


@router.get("/{payment_id}/chain")
def transaction_chain(
    payment_id: str,
    db: Session = Depends(get_db),
) -> Any:
    """
    Traces the full Order -> Payment -> Refund -> Settlement -> Bank chain
    for a given Razorpay payment ID.  The chain includes a break-point
    indicator so the frontend can highlight where the money stopped.
    """
    return trace_transaction_chain(db=db, payment_id=payment_id)
