from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import BigInteger, create_engine, event, select
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker

from app.core.reconciliation import run_reconciliation
from app.core.seeder import seed_data
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.entities import (
    BankTransaction,
    Fee,
    Order,
    Payment,
    ReconciliationException,
    Settlement,
    SettlementItem,
)


@compiles(BigInteger, "sqlite")
def compile_big_integer(element, compiler, **kw):
    return "INTEGER"

client = TestClient(app)

@pytest.fixture
def mock_db():
    db = MagicMock()
    # Mock empty db so seeder can proceed
    db.execute.return_value.scalar_one_or_none.return_value = None
    db.execute.return_value.scalars.return_value.all.return_value = []
    return db

def override_get_db(mock_db):
    def _override():
        yield mock_db
    return _override

@patch("app.core.seeder.get_settings")
@patch("app.core.seeder.razorpay.Client")
def test_seed_endpoint(mock_rzp_client, mock_get_settings, mock_db):
    mock_settings = MagicMock()
    mock_settings.razorpay_key_id = "test_key"
    mock_settings.razorpay_key_secret = "test_secret"
    mock_get_settings.return_value = mock_settings

    mock_client_instance = MagicMock()
    mock_rzp_client.return_value = mock_client_instance

    # Mock responses
    mock_client_instance.payment.all.return_value = {
        "items": [
            {
                "id": "pay_1",
                "amount": 10000,
                "fee": 200,
                "tax": 36,
                "status": "captured",
                "method": "card",
                "created_at": 1600000000,
                "order_id": "order_1"
            },
            {
                "id": "pay_2",
                "amount": 50000,
                "fee": 1000,
                "tax": 180,
                "status": "captured",
                "method": "upi",
                "created_at": 1600000000,
                "order_id": "order_2"
            }
        ]
    }
    
    mock_client_instance.order.fetch.return_value = {
        "id": "order_1",
        "amount": 10000,
        "currency": "INR",
        "status": "paid",
        "receipt": "rcpt_1",
        "created_at": 1600000000
    }
    
    app.dependency_overrides[get_db] = override_get_db(mock_db)
    
    response = client.post("/api/admin/seed")
    
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Seeding completed"
    assert "stats" in data
    
    app.dependency_overrides.clear()


class FakeResult:
    def scalar_one_or_none(self):
        return None

    def scalars(self):
        return self

    def all(self):
        return []


class FakeSession:
    def __init__(self):
        self.objects = []
        self.rollback_called = False

    def execute(self, _statement):
        return FakeResult()

    def add(self, obj):
        self.objects.append(obj)

    def flush(self):
        for index, obj in enumerate(self.objects, start=1):
            if getattr(obj, "id", None) is None:
                obj.id = index

    def commit(self):
        pass

    def rollback(self):
        self.rollback_called = True


@patch("app.core.seeder.get_settings")
@patch("app.core.seeder.razorpay.Client")
def test_seed_creates_order_before_missing_payment_when_razorpay_is_empty(
    mock_rzp_client, mock_get_settings
):
    mock_get_settings.return_value = MagicMock(
        razorpay_key_id="test_key",
        razorpay_key_secret="test_secret",
    )
    mock_rzp_client.return_value.payment.all.return_value = {"items": []}
    db = FakeSession()

    seed_data(db=db)

    orders = [obj for obj in db.objects if isinstance(obj, Order)]
    payments = [obj for obj in db.objects if isinstance(obj, Payment)]
    missing_payment = next(payment for payment in payments if payment.razorpay_payment_id == "pay_miss_50k")
    assert orders
    assert missing_payment.order_id == orders[0].id
    assert db.rollback_called is False


@patch("app.core.seeder.get_settings")
@patch("app.core.seeder.razorpay.Client")
def test_seed_rolls_back_when_persistence_fails(mock_rzp_client, mock_get_settings):
    mock_get_settings.return_value = MagicMock(
        razorpay_key_id="test_key",
        razorpay_key_secret="test_secret",
    )
    mock_rzp_client.return_value.payment.all.side_effect = RuntimeError("persistence setup failure")
    db = FakeSession()

    with pytest.raises(RuntimeError, match="persistence setup failure"):
        seed_data(db=db)

    assert db.rollback_called is True


@pytest.fixture
def sqlite_session():
    engine = create_engine("sqlite:///:memory:")
    def configure_sqlite(connection, _):
        connection.execute("PRAGMA foreign_keys=ON")
        connection.create_function("char_length", 1, len)

    event.listen(engine, "connect", configure_sqlite)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@patch("app.core.seeder.get_settings")
@patch("app.core.seeder.razorpay.Client")
def test_empty_razorpay_response_creates_all_six_demo_anomaly_slots(
    mock_rzp_client, mock_get_settings, sqlite_session
):
    mock_get_settings.return_value = MagicMock(
        razorpay_key_id="test_key",
        razorpay_key_secret="test_secret",
    )
    mock_rzp_client.return_value.payment.all.return_value = {"items": []}

    stats = seed_data(db=sqlite_session)
    payments = sqlite_session.execute(select(Payment)).scalars().all()
    orders = sqlite_session.execute(select(Order)).scalars().all()
    settlements = sqlite_session.execute(select(Settlement)).scalars().all()

    assert stats["payments_created"] == 16
    assert {payment.razorpay_payment_id for payment in payments} == {
        "pay_miss_50k",
        "pay_synth_delayed",
        "pay_synth_partial",
        "pay_synth_duplicate",
        "pay_synth_fee_mismatch",
        "pay_synth_bank_mismatch",
        *(f"pay_synth_clean_{index:02d}" for index in range(1, 11)),
    }
    assert all(payment.order_id in {order.id for order in orders} for payment in payments)
    assert sqlite_session.execute(select(Fee)).scalars().all()
    settlement_types = [settlement.status.value for settlement in settlements]
    assert len(settlements) == 15
    assert set(settlement_types) == {"processing", "processed"}
    assert len(sqlite_session.execute(select(BankTransaction)).scalars().all()) == 14

    partial = next(payment for payment in payments if payment.razorpay_payment_id == "pay_synth_partial")
    partial_item = sqlite_session.execute(
        select(SettlementItem).where(
            SettlementItem.payment_id == partial.id,
            SettlementItem.entry_type == "payment",
        )
    ).scalars().first()
    assert partial_item.amount == partial.amount - partial.fee - Decimal("100.00")

    bank_mismatch = next(payment for payment in payments if payment.razorpay_payment_id == "pay_synth_bank_mismatch")
    bank_settlement = next(item.settlement for item in bank_mismatch.settlement_items)
    bank_transaction = bank_settlement.bank_transactions[0]
    assert bank_transaction.amount != bank_settlement.amount

    run_reconciliation(sqlite_session)
    exception_types = {
        exception.type.value
        for exception in sqlite_session.query(ReconciliationException).all()
    }
    assert exception_types == {
        "delayed_settlement",
        "missing_settlement",
        "partial_settlement",
        "duplicate",
        "fee_mismatch",
        "bank_credit_mismatch",
    }


@patch("app.core.seeder.get_settings")
@patch("app.core.seeder.razorpay.Client")
def test_empty_razorpay_seed_is_idempotent(mock_rzp_client, mock_get_settings, sqlite_session):
    mock_get_settings.return_value = MagicMock(
        razorpay_key_id="test_key",
        razorpay_key_secret="test_secret",
    )
    mock_rzp_client.return_value.payment.all.return_value = {"items": []}

    first_stats = seed_data(db=sqlite_session)
    first_counts = {
        model.__tablename__: sqlite_session.query(model).count()
        for model in (Order, Payment, Fee, Settlement, SettlementItem, BankTransaction)
    }
    second_stats = seed_data(db=sqlite_session)
    second_counts = {
        model.__tablename__: sqlite_session.query(model).count()
        for model in (Order, Payment, Fee, Settlement, SettlementItem, BankTransaction)
    }

    assert first_stats["payments_created"] == 16
    assert second_stats["payments_created"] == 0
    assert first_counts == second_counts
