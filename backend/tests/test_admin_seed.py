from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.core.seeder import seed_data
from app.db.session import get_db
from app.main import app
from app.models.entities import Order, Payment

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
