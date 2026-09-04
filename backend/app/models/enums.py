from __future__ import annotations

from enum import Enum


class OrderStatus(str, Enum):
    CREATED = "created"
    ATTEMPTED = "attempted"
    PAID = "paid"


class PaymentStatus(str, Enum):
    CREATED = "created"
    AUTHORIZED = "authorized"
    CAPTURED = "captured"
    REFUNDED = "refunded"
    FAILED = "failed"


class RefundStatus(str, Enum):
    PENDING = "pending"
    PROCESSED = "processed"
    FAILED = "failed"


class FeeType(str, Enum):
    GATEWAY_FEE = "gateway_fee"
    GST = "gst"
    OTHER = "other"


class SettlementStatus(str, Enum):
    PROCESSED = "processed"
    PROCESSING = "processing"
    ON_HOLD = "on_hold"


class SettlementItemEntryType(str, Enum):
    PAYMENT = "payment"
    REFUND = "refund"
    FEE_DEDUCTION = "fee_deduction"


class PaymentReconciliationStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    DELAYED = "delayed"
    SETTLED = "settled"
    HELD = "held"
    MATCHED = "matched"
    FALLBACK_MATCHED = "fallback_matched"
    PARTIALLY_MATCHED = "partially_matched"
    DUPLICATE_FLAGGED = "duplicate_flagged"
    MISSING = "missing"
    FEE_MISMATCH = "fee_mismatch"
    BANK_MISMATCH = "bank_mismatch"


class ExceptionType(str, Enum):
    DELAYED_SETTLEMENT = "delayed_settlement"
    MISSING_SETTLEMENT = "missing_settlement"
    PARTIAL_SETTLEMENT = "partial_settlement"
    DUPLICATE = "duplicate"
    FEE_MISMATCH = "fee_mismatch"
    BANK_CREDIT_MISMATCH = "bank_credit_mismatch"
    UNUSUAL_PATTERN = "unusual_pattern"


class ExceptionSeverity(str, Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class ExceptionStatus(str, Enum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
