from __future__ import annotations

from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.intelligence import get_dashboard_summary
from app.db.session import get_db

router = APIRouter()


@router.get("/summary")
def dashboard_summary(
    target_date: str | None = Query(None, description="ISO date (YYYY-MM-DD); defaults to today"),
    db: Session = Depends(get_db),
) -> Any:
    """
    Returns high-level financial totals for the requested date plus open exception
    count and top-3 exception previews.

    Totals:
      - expected  = captured payments - refunds - fees
      - settled   = Sum of settlement amounts whose expected_date equals the date
      - received  = Sum of bank_transaction amounts credited on that date
    """
    parsed_date: date | None = None
    if target_date:
        try:
            parsed_date = date.fromisoformat(target_date)
        except ValueError:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid date format '{target_date}'. Use YYYY-MM-DD.",
            )

    return get_dashboard_summary(db=db, target_date=parsed_date)

