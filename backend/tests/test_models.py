from __future__ import annotations

from app import models  # noqa: F401
from app.db.base import Base


def test_phase_one_tables_are_registered() -> None:
    assert set(Base.metadata.tables.keys()) == {
        "orders",
        "payments",
        "refunds",
        "fees",
        "settlements",
        "settlement_items",
        "bank_transactions",
        "reconciliation_exceptions",
    }


def test_required_indexes_exist() -> None:
    indexes = {index.name for table in Base.metadata.tables.values() for index in table.indexes}

    assert "ix_payments_reconciliation_status" in indexes
    assert "ix_settlement_items_payment_entry_type" in indexes
    assert "ix_reconciliation_exceptions_type_status" in indexes
    assert "ix_bank_transactions_settlement_id" in indexes


def test_required_foreign_keys_exist() -> None:
    foreign_keys = {
        foreign_key.constraint.name
        for table in Base.metadata.tables.values()
        for foreign_key in table.foreign_keys
    }

    assert "fk_payments_order_id" in foreign_keys
    assert "fk_refunds_payment_id" in foreign_keys
    assert "fk_settlement_items_settlement_id" in foreign_keys
    assert "fk_bank_transactions_settlement_id" in foreign_keys
