from __future__ import annotations

from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.admin import router as admin_router

def create_app() -> FastAPI:
    app = FastAPI(
        title="Razorpay Financial Intelligence",
        version="0.1.0",
    )
    app.include_router(health_router, tags=["Health"])
    app.include_router(admin_router, prefix="/api/admin", tags=["Admin"])
    return app


app = create_app()
