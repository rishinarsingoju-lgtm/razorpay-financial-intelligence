from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.seeder import seed_data
from app.db.session import get_db

router = APIRouter()


@router.post("/seed")
def seed_database(db: Session = Depends(get_db)):
    """
    DEV ONLY: Fetch Razorpay test data and generate synthetic settlements.
    Idempotent operation.
    """
    stats = seed_data(db=db)
    return {"message": "Seeding completed", "stats": stats}

@router.post("/reconcile")
def run_reconciliation_job(db: Session = Depends(get_db)):
    """
    DEV ONLY: Run the reconciliation engine manually.
    Idempotently recalculates and creates exception records.
    """
    from app.core.reconciliation import run_reconciliation
    stats = run_reconciliation(db=db)
    return {"message": "Reconciliation completed", "stats": stats}
