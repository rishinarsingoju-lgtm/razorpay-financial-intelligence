from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from app.main import app
from app.db.session import get_db

client = TestClient(app)

@pytest.fixture
def mock_db():
    db = MagicMock()
    # Mock some data if needed, or just let it pass with empty lists
    db.execute.return_value.scalars.return_value.all.return_value = []
    return db

def override_get_db(mock_db):
    def _override():
        yield mock_db
    return _override

def test_reconcile_endpoint(mock_db):
    app.dependency_overrides[get_db] = override_get_db(mock_db)
    
    response = client.post("/api/admin/reconcile")
    
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Reconciliation completed"
    assert "stats" in data
    
    app.dependency_overrides.clear()

def test_get_exceptions_endpoint(mock_db):
    app.dependency_overrides[get_db] = override_get_db(mock_db)
    
    response = client.get("/api/exceptions/")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    
    app.dependency_overrides.clear()
