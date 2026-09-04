from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import get_settings
from app.db.check import check_database_connection

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, bool | str]:
    settings = get_settings()
    return {
        "status": "ok",
        "service": "razorpay-financial-intelligence-backend",
        "database_configured": settings.database_url_configured,
    }


@router.get("/health/database")
def database_health() -> dict[str, str]:
    try:
        check_database_connection()
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection failed.",
        ) from exc

    return {"status": "ok"}
