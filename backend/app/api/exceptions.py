from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.entities import ReconciliationException
from app.models.enums import ExceptionSeverity, ExceptionStatus, ExceptionType

router = APIRouter()

@router.get("/")
def get_exceptions(
    type: ExceptionType | None = Query(None),
    severity: ExceptionSeverity | None = Query(None),
    status: ExceptionStatus | None = Query(None),
    db: Session = Depends(get_db)
) -> Any:
    stmt = select(ReconciliationException)
    if type:
        stmt = stmt.filter(ReconciliationException.type == type)
    if severity:
        stmt = stmt.filter(ReconciliationException.severity == severity)
    if status:
        stmt = stmt.filter(ReconciliationException.status == status)
    
    stmt = stmt.order_by(ReconciliationException.detected_at.desc())
    exceptions = db.execute(stmt).scalars().all()
    
    return [
        {
            "id": exc.id,
            "type": exc.type.value,
            "severity": exc.severity.value,
            "status": exc.status.value,
            "expected_amount": exc.expected_amount,
            "actual_amount": exc.actual_amount,
            "discrepancy": exc.discrepancy,
            "description": exc.description,
            "detected_at": exc.detected_at,
            "related_order_id": exc.related_order_id,
            "related_payment_id": exc.related_payment_id,
            "related_settlement_id": exc.related_settlement_id,
        }
        for exc in exceptions
    ]

@router.patch("/{exception_id}")
def update_exception_status(
    exception_id: int,
    status: ExceptionStatus,
    db: Session = Depends(get_db)
) -> Any:
    exc = db.execute(select(ReconciliationException).filter_by(id=exception_id)).scalar_one_or_none()
    if not exc:
        raise HTTPException(status_code=404, detail="Exception not found")
    
    exc.status = status
    db.commit()
    return {"message": "Status updated successfully", "status": exc.status.value}
