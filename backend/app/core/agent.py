"""
Gemini AI Copilot agent.

Design contract (from PROJECT_SPEC.md):
  - Single Gemini agent; no multi-agent orchestration.
  - Must call a tool before stating any financial figure.
  - Never estimates or performs its own arithmetic.
  - Cites specific record IDs in every answer.
  - Exactly 5 tools -- same names as spec, delegating to the shared
    intelligence service layer so REST endpoints and AI answers are always
    in sync.
  - Agent must never trigger writes.
"""
from __future__ import annotations

import logging
from typing import Any

from google import genai
from google.genai import types

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tool definitions (sent to Gemini as function declarations)
# ---------------------------------------------------------------------------

_TOOL_DECLARATIONS = [
    types.FunctionDeclaration(
        name="query_transactions",
        description=(
            "Find payment transactions that match the given filters. "
            "Call this before quoting any payment amount or listing transactions."
        ),
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "amount_min": types.Schema(type=types.Type.NUMBER, description="Minimum amount in INR paise"),
                "amount_max": types.Schema(type=types.Type.NUMBER, description="Maximum amount in INR paise"),
                "status": types.Schema(type=types.Type.STRING, description="Reconciliation status filter"),
                "date_from": types.Schema(type=types.Type.STRING, description="ISO datetime lower bound"),
                "date_to": types.Schema(type=types.Type.STRING, description="ISO datetime upper bound"),
                "unmatched_only": types.Schema(type=types.Type.BOOLEAN, description="Only unmatched/unsettled payments"),
            },
        ),
    ),
    types.FunctionDeclaration(
        name="get_exceptions",
        description=(
            "List reconciliation exceptions. "
            "Call this to look up anomalies, discrepancies, or exception details."
        ),
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "type": types.Schema(type=types.Type.STRING, description="Exception type filter"),
                "severity": types.Schema(type=types.Type.STRING, description="critical | warning | info"),
                "date_from": types.Schema(type=types.Type.STRING, description="ISO datetime lower bound"),
                "date_to": types.Schema(type=types.Type.STRING, description="ISO datetime upper bound"),
                "status": types.Schema(type=types.Type.STRING, description="open | investigating | resolved"),
            },
        ),
    ),
    types.FunctionDeclaration(
        name="get_settlement_status",
        description=(
            "Get settlement-level health: amounts, status, and dates. "
            "Call this for any question about a specific settlement batch."
        ),
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "settlement_id": types.Schema(type=types.Type.STRING, description="Razorpay settlement ID"),
                "date_range": types.Schema(type=types.Type.STRING, description="ISO date range hint"),
            },
        ),
    ),
    types.FunctionDeclaration(
        name="compare_periods",
        description=(
            "Compare aggregate financial totals between two date ranges. "
            "Call this for questions like why is today lower than yesterday."
        ),
        parameters=types.Schema(
            type=types.Type.OBJECT,
            required=["period_a_start", "period_a_end", "period_b_start", "period_b_end"],
            properties={
                "period_a_start": types.Schema(type=types.Type.STRING, description="ISO datetime start of period A"),
                "period_a_end": types.Schema(type=types.Type.STRING, description="ISO datetime end of period A"),
                "period_b_start": types.Schema(type=types.Type.STRING, description="ISO datetime start of period B"),
                "period_b_end": types.Schema(type=types.Type.STRING, description="ISO datetime end of period B"),
            },
        ),
    ),
    types.FunctionDeclaration(
        name="trace_transaction_chain",
        description=(
            "Trace the full Order -> Payment -> Refund -> Settlement -> Bank chain "
            "for a payment. Call this when asked where money is or why it is missing."
        ),
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "payment_id": types.Schema(type=types.Type.STRING, description="Razorpay payment ID (pay_xxx)"),
                "order_id": types.Schema(type=types.Type.STRING, description="Razorpay order ID (order_xxx)"),
            },
        ),
    ),
]

_SYSTEM_PROMPT = """\
You are the AI Copilot for a financial reconciliation platform built on Razorpay data.

RULES -- follow them strictly:
1. You MUST call a tool before stating any financial figure or referencing any record.
2. Never perform arithmetic yourself. All numbers come from tool results.
3. Cite specific record IDs (exception ID, payment ID, settlement ID) in every answer.
4. If a tool returns an empty list or error, say so explicitly -- never fabricate data.
5. You may call multiple tools in sequence to build a complete answer.
6. Never trigger any write operations -- you are read-only.

When asked about a lower settlement, call compare_periods then get_exceptions.
When asked where money is missing, call query_transactions then trace_transaction_chain.
When asked about anomalies, call get_exceptions.
When asked about a specific settlement, call get_settlement_status.
"""


# ---------------------------------------------------------------------------
# Tool dispatcher  (maps function names -> intelligence service calls)
# ---------------------------------------------------------------------------

def _dispatch_tool(name: str, args: dict[str, Any], db: Any) -> Any:
    """
    Calls the matching intelligence service function.
    The DB session is passed here so tools share the same transaction as the
    REST request -- numbers are identical between API and AI answers.
    """
    from app.core import intelligence

    if name == "query_transactions":
        return intelligence.query_transactions(db=db, **args)
    elif name == "get_exceptions":
        return intelligence.get_exceptions_info(db=db, **args)
    elif name == "get_settlement_status":
        return intelligence.get_settlement_status(db=db, **args)
    elif name == "compare_periods":
        return intelligence.compare_periods(db=db, **args)
    elif name == "trace_transaction_chain":
        return intelligence.trace_transaction_chain(db=db, **args)
    else:
        return {"error": f"Unknown tool: {name}"}


# ---------------------------------------------------------------------------
# Helper: extract referenced IDs from tool results
# ---------------------------------------------------------------------------

def _extract_ids(data: Any, ids: list[str]) -> None:
    """Recursively pull out values from ID-bearing keys."""
    if isinstance(data, dict):
        for key, value in data.items():
            if key in (
                "id",
                "razorpay_payment_id",
                "razorpay_settlement_id",
                "razorpay_refund_id",
                "related_payment_id",
            ):
                if value is not None:
                    ids.append(str(value))
            else:
                _extract_ids(value, ids)
    elif isinstance(data, list):
        for item in data:
            _extract_ids(item, ids)


# ---------------------------------------------------------------------------
# Main agent entry point
# ---------------------------------------------------------------------------

def run_copilot(question: str, db: Any) -> dict[str, Any]:
    """
    Runs a single Gemini agent turn with function-calling enabled.

    The agent may call multiple tools before producing a final text answer.
    All tool calls delegate to intelligence.py so REST and AI numbers are
    always identical.

    Returns:
        {
            "answer": str,
            "tool_calls_made": [{"tool": str, "args": dict}, ...],
            "referenced_ids": [str, ...],
        }
    """
    settings = get_settings()
    if not settings.gemini_api_key:
        return {
            "answer": (
                "AI Copilot is not configured. "
                "Please set GEMINI_API_KEY in your .env file."
            ),
            "tool_calls_made": [],
            "referenced_ids": [],
        }

    client = genai.Client(api_key=settings.gemini_api_key)

    tool_calls_made: list[dict] = []
    referenced_ids: list[str] = []

    contents: list[types.Content] = [
        types.Content(role="user", parts=[types.Part(text=question)])
    ]

    tools = types.Tool(function_declarations=_TOOL_DECLARATIONS)

    # Agentic loop -- keep calling until the model stops requesting tool calls
    max_iterations = 10
    for _ in range(max_iterations):
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=_SYSTEM_PROMPT,
                tools=[tools],
                temperature=0.0,
                thinking_config=types.ThinkingConfig(include_thoughts=False),
            ),
        )

        candidate = response.candidates[0]
        contents.append(candidate.content)


        function_calls = [p for p in candidate.content.parts if p.function_call is not None]

        if not function_calls:
            text_parts = [p.text for p in candidate.content.parts if p.text]
            answer = "\n".join(text_parts).strip()
            return {
                "answer": answer,
                "tool_calls_made": tool_calls_made,
                "referenced_ids": list(dict.fromkeys(referenced_ids)),
            }

        tool_result_parts: list[types.Part] = []
        for fc in function_calls:
            tool_name = fc.function_call.name
            tool_args = dict(fc.function_call.args) if fc.function_call.args else {}

            logger.info("Copilot tool call: %s(%s)", tool_name, tool_args)
            tool_calls_made.append({"tool": tool_name, "args": tool_args})

            result = _dispatch_tool(tool_name, tool_args, db)
            _extract_ids(result, referenced_ids)

            tool_result_parts.append(
                types.Part(
                    function_response=types.FunctionResponse(
                        name=tool_name,
                        response={"result": result},
                    )
                )
            )

        contents.append(types.Content(role="user", parts=tool_result_parts))

    return {
        "answer": (
            "I reached the maximum number of tool calls without a final answer. "
            "Please try a more specific question."
        ),
        "tool_calls_made": tool_calls_made,
        "referenced_ids": list(dict.fromkeys(referenced_ids)),
    }
