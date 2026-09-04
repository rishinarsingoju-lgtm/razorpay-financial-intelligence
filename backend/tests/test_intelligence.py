"""
Tests for Phase 4: Financial intelligence service functions and API endpoints.

All tests use a mock DB session so no real PostgreSQL connection is required.
The agent (copilot) tests mock the Gemini client so no API key is needed.
"""
from __future__ import annotations

from decimal import Decimal
from datetime import date, datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import get_db

client = TestClient(app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def override_get_db(mock_db):
    def _override():
        yield mock_db
    return _override


def _mock_exception(
    exc_id=1,
    exc_type="missing_settlement",
    severity="critical",
    status="open",
    discrepancy=50000,
    description="Missing settlement for payment pay_test",
    payment=None,
):
    exc = MagicMock()
    exc.id = exc_id
    exc.type = MagicMock()
    exc.type.value = exc_type
    exc.severity = MagicMock()
    exc.severity.value = severity
    exc.status = MagicMock()
    exc.status.value = status
    exc.discrepancy = Decimal(str(discrepancy))
    exc.description = description
    exc.related_payment = payment
    exc.expected_amount = Decimal("50000")
    exc.actual_amount = Decimal("0")
    exc.detected_at = datetime(2024, 1, 15, 10, 0, 0)
    exc.related_order_id = None
    exc.related_payment_id = 1 if payment else None
    exc.related_settlement_id = None
    return exc


def _mock_payment(pay_id="pay_test123", amount=50000):
    p = MagicMock()
    p.id = 1
    p.razorpay_payment_id = pay_id
    p.amount = Decimal(str(amount))
    p.status = MagicMock()
    p.status.value = "captured"
    p.reconciliation_status = MagicMock()
    p.reconciliation_status.value = "missing"
    p.created_at = datetime(2024, 1, 10, 12, 0, 0)
    p.refunds = []
    p.fees = []
    p.settlement_items = []
    p.order = MagicMock()
    p.order.razorpay_order_id = "order_test123"
    p.order.amount = Decimal(str(amount))
    p.order.status = MagicMock()
    p.order.status.value = "paid"
    return p


def _mock_settlement(settle_id="setl_test001", amount=100000, status="processed"):
    s = MagicMock()
    s.id = 1
    s.razorpay_settlement_id = settle_id
    s.amount = Decimal(str(amount))
    s.status = MagicMock()
    s.status.value = status
    s.expected_date = date(2024, 1, 12)
    s.processed_date = date(2024, 1, 12) if status == "processed" else None
    s.items = []
    s.bank_transactions = []
    return s


# ===========================================================================
# Dashboard endpoint tests
# ===========================================================================

class TestDashboardSummary:

    def test_summary_returns_200(self):
        """GET /api/dashboard/summary should return 200 with required fields."""
        mock_db = MagicMock()
        # exception count
        mock_db.execute.return_value.scalar_one.return_value = 3
        mock_db.execute.return_value.scalars.return_value.all.return_value = []

        app.dependency_overrides[get_db] = override_get_db(mock_db)
        try:
            response = client.get("/api/dashboard/summary")
            assert response.status_code == 200
            data = response.json()
            assert "totals" in data
            assert "exception_count" in data
            assert "top_exceptions" in data
        finally:
            app.dependency_overrides.clear()

    def test_summary_with_date_param(self):
        """Dashboard should accept an optional target_date query param."""
        mock_db = MagicMock()
        mock_db.execute.return_value.scalar_one.return_value = 0
        mock_db.execute.return_value.scalars.return_value.all.return_value = []

        app.dependency_overrides[get_db] = override_get_db(mock_db)
        try:
            response = client.get("/api/dashboard/summary?target_date=2024-01-15")
            assert response.status_code == 200
        finally:
            app.dependency_overrides.clear()

    def test_summary_invalid_date_returns_422(self):
        """An invalid date format should return 422 Unprocessable Entity."""
        mock_db = MagicMock()
        app.dependency_overrides[get_db] = override_get_db(mock_db)
        try:
            response = client.get("/api/dashboard/summary?target_date=not-a-date")
            assert response.status_code == 422
        finally:
            app.dependency_overrides.clear()

    def test_summary_top_exceptions_included(self):
        """Top exceptions list should include type, severity, and description."""
        mock_db = MagicMock()
        exc = _mock_exception()

        # The intelligence function calls db.execute multiple times.
        # We use side_effect to return different mock results in sequence.
        scalar_one_result = MagicMock()
        scalar_one_result.scalar_one.return_value = 2
        scalars_result = MagicMock()
        scalars_result.scalars.return_value.all.return_value = [exc]

        mock_db.execute.side_effect = [scalar_one_result, scalars_result] + [
            MagicMock(scalar_one=MagicMock(return_value=Decimal("0")))
        ] * 10

        app.dependency_overrides[get_db] = override_get_db(mock_db)
        try:
            response = client.get("/api/dashboard/summary")
            assert response.status_code == 200
        finally:
            app.dependency_overrides.clear()


# ===========================================================================
# Transactions endpoint tests
# ===========================================================================

class TestTransactionsEndpoint:

    def test_list_transactions_returns_200(self):
        """GET /api/transactions/ should return a list."""
        mock_db = MagicMock()
        mock_db.execute.return_value.scalars.return_value.all.return_value = []

        app.dependency_overrides[get_db] = override_get_db(mock_db)
        try:
            response = client.get("/api/transactions/")
            assert response.status_code == 200
            assert isinstance(response.json(), list)
        finally:
            app.dependency_overrides.clear()

    def test_list_transactions_with_filters(self):
        """Filters should be accepted without error."""
        mock_db = MagicMock()
        mock_db.execute.return_value.scalars.return_value.all.return_value = []

        app.dependency_overrides[get_db] = override_get_db(mock_db)
        try:
            response = client.get(
                "/api/transactions/?amount_min=1000&amount_max=100000&unmatched_only=true"
            )
            assert response.status_code == 200
        finally:
            app.dependency_overrides.clear()

    def test_chain_not_found(self):
        """GET /api/transactions/{id}/chain should return error dict when not found."""
        mock_db = MagicMock()
        mock_db.execute.return_value.scalar_one_or_none.return_value = None

        app.dependency_overrides[get_db] = override_get_db(mock_db)
        try:
            response = client.get("/api/transactions/pay_nonexistent/chain")
            assert response.status_code == 200
            data = response.json()
            assert "error" in data
        finally:
            app.dependency_overrides.clear()

    def test_chain_found(self):
        """GET /api/transactions/{id}/chain should return chain dict when found."""
        mock_db = MagicMock()
        payment = _mock_payment()
        mock_db.execute.return_value.scalar_one_or_none.return_value = payment

        app.dependency_overrides[get_db] = override_get_db(mock_db)
        try:
            response = client.get("/api/transactions/pay_test123/chain")
            assert response.status_code == 200
            data = response.json()
            assert "order" in data
            assert "payment" in data
        finally:
            app.dependency_overrides.clear()


# ===========================================================================
# Settlements endpoint tests
# ===========================================================================

class TestSettlementsEndpoint:

    def test_list_settlements_returns_200(self):
        """GET /api/settlements/ should return a list."""
        mock_db = MagicMock()
        mock_db.execute.return_value.scalars.return_value.all.return_value = []

        app.dependency_overrides[get_db] = override_get_db(mock_db)
        try:
            response = client.get("/api/settlements/")
            assert response.status_code == 200
            assert isinstance(response.json(), list)
        finally:
            app.dependency_overrides.clear()

    def test_settlement_detail_not_found(self):
        """GET /api/settlements/{id} should 404 for unknown ID."""
        mock_db = MagicMock()
        mock_db.execute.return_value.scalar_one_or_none.return_value = None

        app.dependency_overrides[get_db] = override_get_db(mock_db)
        try:
            response = client.get("/api/settlements/9999")
            assert response.status_code == 404
        finally:
            app.dependency_overrides.clear()

    def test_settlement_detail_found(self):
        """GET /api/settlements/{id} should return settlement detail."""
        mock_db = MagicMock()
        s = _mock_settlement()
        mock_db.execute.return_value.scalar_one_or_none.return_value = s

        app.dependency_overrides[get_db] = override_get_db(mock_db)
        try:
            response = client.get("/api/settlements/1")
            assert response.status_code == 200
            data = response.json()
            assert "amount" in data
            assert "status" in data
            assert "items" in data
            assert "bank_transactions" in data
        finally:
            app.dependency_overrides.clear()

    def test_days_overdue_computed(self):
        """Processing settlements past expected_date should have days_overdue > 0."""
        mock_db = MagicMock()
        s = _mock_settlement(status="processing")
        s.status.value = "processing"
        s.expected_date = date(2020, 1, 1)  # far in the past
        mock_db.execute.return_value.scalars.return_value.all.return_value = [s]

        app.dependency_overrides[get_db] = override_get_db(mock_db)
        try:
            response = client.get("/api/settlements/")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["days_overdue"] > 0
        finally:
            app.dependency_overrides.clear()


# ===========================================================================
# Intelligence service layer unit tests
# ===========================================================================

class TestIntelligenceServiceLayer:

    def test_query_transactions_returns_list(self):
        from app.core.intelligence import query_transactions

        mock_db = MagicMock()
        mock_db.execute.return_value.scalars.return_value.all.return_value = []
        result = query_transactions(db=mock_db)
        assert isinstance(result, list)

    def test_get_exceptions_info_returns_list(self):
        from app.core.intelligence import get_exceptions_info

        mock_db = MagicMock()
        mock_db.execute.return_value.scalars.return_value.all.return_value = []
        result = get_exceptions_info(db=mock_db)
        assert isinstance(result, list)

    def test_get_settlement_status_returns_list(self):
        from app.core.intelligence import get_settlement_status

        mock_db = MagicMock()
        mock_db.execute.return_value.scalars.return_value.all.return_value = []
        result = get_settlement_status(db=mock_db)
        assert isinstance(result, list)

    def test_compare_periods_structure(self):
        from app.core.intelligence import compare_periods

        mock_db = MagicMock()
        mock_db.execute.return_value.scalar_one.return_value = Decimal("1000")
        result = compare_periods(
            db=mock_db,
            period_a_start="2024-01-01T00:00:00",
            period_a_end="2024-01-07T23:59:59",
            period_b_start="2024-01-08T00:00:00",
            period_b_end="2024-01-14T23:59:59",
        )
        assert "period_a" in result
        assert "period_b" in result
        assert "net_amount" in result["period_a"]

    def test_trace_transaction_chain_not_found(self):
        from app.core.intelligence import trace_transaction_chain

        mock_db = MagicMock()
        mock_db.execute.return_value.scalar_one_or_none.return_value = None
        result = trace_transaction_chain(db=mock_db, payment_id="pay_nonexistent")
        assert "error" in result

    def test_trace_transaction_chain_found(self):
        from app.core.intelligence import trace_transaction_chain

        mock_db = MagicMock()
        payment = _mock_payment()
        mock_db.execute.return_value.scalar_one_or_none.return_value = payment
        result = trace_transaction_chain(db=mock_db, payment_id="pay_test123")
        assert "order" in result
        assert "payment" in result
        assert "settlements" in result


# ===========================================================================
# Copilot endpoint tests
# ===========================================================================

class TestCopilotEndpoint:

    def test_copilot_missing_api_key(self):
        """Without GEMINI_API_KEY the endpoint should return a friendly message."""
        mock_db = MagicMock()

        app.dependency_overrides[get_db] = override_get_db(mock_db)
        try:
            with patch("app.core.agent.get_settings") as mock_settings_fn:
                mock_settings = MagicMock()
                mock_settings.gemini_api_key = None
                mock_settings_fn.return_value = mock_settings

                response = client.post(
                    "/api/copilot/ask",
                    json={"question": "Why is today settlement lower?"},
                )
                assert response.status_code == 200
                data = response.json()
                assert "answer" in data
                assert "GEMINI_API_KEY" in data["answer"]
        finally:
            app.dependency_overrides.clear()

    def test_copilot_missing_question_returns_422(self):
        """Empty body should fail validation."""
        response = client.post("/api/copilot/ask", json={})
        assert response.status_code == 422

    def test_copilot_tool_calls_dispatched(self):
        """With a mocked Gemini client the tool dispatch loop should run."""
        mock_db = MagicMock()
        mock_db.execute.return_value.scalars.return_value.all.return_value = []

        app.dependency_overrides[get_db] = override_get_db(mock_db)
        try:
            with patch("app.core.agent.get_settings") as mock_settings_fn, \
                 patch("app.core.agent.genai.Client") as mock_genai_client:

                mock_settings = MagicMock()
                mock_settings.gemini_api_key = "fake_key"
                mock_settings_fn.return_value = mock_settings

                # First response: model requests a tool call
                fc_part = MagicMock()
                fc_part.function_call = MagicMock()
                fc_part.function_call.name = "get_exceptions"
                fc_part.function_call.args = {}
                fc_part.text = None

                first_candidate = MagicMock()
                first_candidate.content = MagicMock()
                first_candidate.content.parts = [fc_part]

                # Second response: model returns final text
                text_part = MagicMock()
                text_part.function_call = None
                text_part.text = "There are no open exceptions right now."

                second_candidate = MagicMock()
                second_candidate.content = MagicMock()
                second_candidate.content.parts = [text_part]

                mock_client_instance = MagicMock()
                mock_client_instance.models.generate_content.side_effect = [
                    MagicMock(candidates=[first_candidate]),
                    MagicMock(candidates=[second_candidate]),
                ]
                mock_genai_client.return_value = mock_client_instance

                response = client.post(
                    "/api/copilot/ask",
                    json={"question": "Are there any exceptions?"},
                )
                assert response.status_code == 200
                data = response.json()
                assert "answer" in data
                assert "tool_calls_made" in data
                assert "referenced_ids" in data
                # The mocked loop should have called get_exceptions once
                assert len(data["tool_calls_made"]) == 1
                assert data["tool_calls_made"][0]["tool"] == "get_exceptions"
                assert data["answer"] == "There are no open exceptions right now."
                request_config = mock_client_instance.models.generate_content.call_args_list[0].kwargs["config"]
                assert request_config.thinking_config.include_thoughts is False
        finally:
            app.dependency_overrides.clear()


# ===========================================================================
# Agent unit tests
# ===========================================================================

class TestAgentDispatch:

    def test_dispatch_query_transactions(self):
        from app.core.agent import _dispatch_tool

        mock_db = MagicMock()
        mock_db.execute.return_value.scalars.return_value.all.return_value = []
        result = _dispatch_tool("query_transactions", {}, mock_db)
        assert isinstance(result, list)

    def test_dispatch_get_exceptions(self):
        from app.core.agent import _dispatch_tool

        mock_db = MagicMock()
        mock_db.execute.return_value.scalars.return_value.all.return_value = []
        result = _dispatch_tool("get_exceptions", {}, mock_db)
        assert isinstance(result, list)

    def test_dispatch_get_settlement_status(self):
        from app.core.agent import _dispatch_tool

        mock_db = MagicMock()
        mock_db.execute.return_value.scalars.return_value.all.return_value = []
        result = _dispatch_tool("get_settlement_status", {}, mock_db)
        assert isinstance(result, list)

    def test_dispatch_unknown_tool(self):
        from app.core.agent import _dispatch_tool

        mock_db = MagicMock()
        result = _dispatch_tool("nonexistent_tool", {}, mock_db)
        assert "error" in result

    def test_extract_ids_flat(self):
        from app.core.agent import _extract_ids

        ids: list[str] = []
        _extract_ids({"razorpay_payment_id": "pay_abc", "amount": 1000}, ids)
        assert "pay_abc" in ids

    def test_extract_ids_nested_list(self):
        from app.core.agent import _extract_ids

        ids: list[str] = []
        data = [
            {"razorpay_payment_id": "pay_1", "amount": 100},
            {"razorpay_payment_id": "pay_2", "amount": 200},
        ]
        _extract_ids(data, ids)
        assert "pay_1" in ids
        assert "pay_2" in ids
