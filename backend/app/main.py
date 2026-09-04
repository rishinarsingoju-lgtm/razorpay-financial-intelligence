from __future__ import annotations

from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.admin import router as admin_router
from app.api.copilot import router as copilot_router
from app.api.dashboard import router as dashboard_router
from app.api.exceptions import router as exceptions_router
from app.api.settlements import router as settlements_router
from app.api.transactions import router as transactions_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Razorpay Financial Intelligence",
        version="0.1.0",
    )
    app.include_router(health_router, tags=["Health"])
    app.include_router(admin_router, prefix="/api/admin", tags=["Admin"])
    app.include_router(dashboard_router, prefix="/api/dashboard", tags=["Dashboard"])
    app.include_router(transactions_router, prefix="/api/transactions", tags=["Transactions"])
    app.include_router(exceptions_router, prefix="/api/exceptions", tags=["Exceptions"])
    app.include_router(settlements_router, prefix="/api/settlements", tags=["Settlements"])
    app.include_router(copilot_router, prefix="/api/copilot", tags=["Copilot"])
    return app


app = create_app()
