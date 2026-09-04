from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app
from app.db.session import get_db

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
