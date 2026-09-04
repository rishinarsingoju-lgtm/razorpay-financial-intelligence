from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.agent import run_copilot
from app.db.session import get_db

router = APIRouter()


class CopilotRequest(BaseModel):
    question: str


@router.post("/ask")
def copilot_ask(
    body: CopilotRequest,
    db: Session = Depends(get_db),
) -> Any:
    """
    Submits a natural-language question to the AI Copilot.

    The agent will call one or more internal tools (grounded in actual DB data)
    before producing a final answer. The response includes:
      - answer: the natural-language response
      - tool_calls_made: which tools were invoked and with what args
      - referenced_ids: payment/settlement/exception IDs cited in the answer

    The agent never performs writes and never fabricates figures -- all
    numbers come from the same service functions used by the REST endpoints.
    """
    result = run_copilot(question=body.question, db=db)
    return result
