from __future__ import annotations

import logging
import random
from datetime import date, datetime, timedelta
from decimal import Decimal

import razorpay
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.entities import (
    BankTransaction,
    Fee,
    Order,
    Payment,
    Refund,
    Settlement,
    SettlementItem,
)
from app.models.enums import (
    FeeType,
    OrderStatus,
    PaymentStatus,
    RefundStatus,
    SettlementItemEntryType,
    SettlementStatus,
)

logger = logging.getLogger(__name__)

def seed_data(db: Session, seed: int = 42) -> dict:
    try:
        return _seed_data(db=db, seed=seed)
    except Exception:
        db.rollback()
        raise


def _seed_data(db: Session, seed: int = 42) -> dict:
    settings = get_settings()
    if not settings.razorpay_key_id or not settings.razorpay_key_secret:
        raise ValueError("Razorpay credentials not found in settings")

    client = razorpay.Client(
        auth=(settings.razorpay_key_id, settings.razorpay_key_secret)
    )

    # 1. Fetch real test data from Razorpay
    fetched_payments = client.payment.all({"count": 30})["items"]

    random.seed(seed)
    
    stats = {
        "orders_created": 0,
        "payments_created": 0,
        "refunds_created": 0,
        "fees_created": 0,
        "settlements_created": 0,
        "settlement_items_created": 0,
        "bank_transactions_created": 0,
    }

    inserted_payments: list[Payment] = []

    for p_data in fetched_payments:
        amount_inr = Decimal(p_data["amount"]) / 100
        fee_inr = Decimal(p_data.get("fee", 0) or 0) / 100
        tax_inr = Decimal(p_data.get("tax", 0) or 0) / 100
        
        created_at_dt = datetime.fromtimestamp(p_data["created_at"])
        
        status_str = p_data["status"]
        if status_str not in [s.value for s in PaymentStatus]:
            status_str = PaymentStatus.CAPTURED.value

        order_id_str = p_data.get("order_id")
        order_obj = None
        if order_id_str:
            order_obj = db.execute(select(Order).filter_by(razorpay_order_id=order_id_str)).scalar_one_or_none()
            if not order_obj:
                try:
                    o_data = client.order.fetch(order_id_str)
                    o_amount = Decimal(o_data["amount"]) / 100
                    o_status = OrderStatus.PAID.value if o_data["status"] == "paid" else OrderStatus.CREATED.value
                    
                    order_obj = Order(
                        razorpay_order_id=order_id_str,
                        amount=o_amount,
                        currency=o_data.get("currency", "INR"),
                        status=o_status,
                        receipt=o_data.get("receipt"),
                        created_at=datetime.fromtimestamp(o_data["created_at"])
                    )
                    db.add(order_obj)
                    db.flush()
                    stats["orders_created"] += 1
                except Exception as e:
                    logger.warning(f"Failed to fetch order {order_id_str}: {e}")

        if not order_obj:
            order_obj = Order(
                razorpay_order_id=order_id_str or f"synth_ord_{p_data['id']}",
                amount=amount_inr,
                currency="INR",
                status=OrderStatus.PAID,
                created_at=created_at_dt
            )
            db.add(order_obj)
            db.flush()
            stats["orders_created"] += 1

        payment_obj = db.execute(select(Payment).filter_by(razorpay_payment_id=p_data["id"])).scalar_one_or_none()
        if not payment_obj:
            payment_obj = Payment(
                razorpay_payment_id=p_data["id"],
                order_id=order_obj.id,
                amount=amount_inr,
                fee=fee_inr,
                tax=tax_inr,
                status=status_str,
                method=p_data.get("method", "card"),
                created_at=created_at_dt
            )
            db.add(payment_obj)
            db.flush()
            stats["payments_created"] += 1
            
            if fee_inr > 0:
                gateway_fee = Fee(
                    payment_id=payment_obj.id,
                    type=FeeType.GATEWAY_FEE,
                    amount=fee_inr - tax_inr
                )
                db.add(gateway_fee)
                
                gst_fee = Fee(
                    payment_id=payment_obj.id,
                    type=FeeType.GST,
                    amount=tax_inr
                )
                db.add(gst_fee)
                db.flush()
                stats["fees_created"] += 2
        
        inserted_payments.append(payment_obj)

        if payment_obj.status in [PaymentStatus.REFUNDED.value, "refunded"]:
            try:
                r_list = client.refund.all({"payment_id": p_data["id"]})["items"]
                for r_data in r_list:
                    refund_obj = db.execute(select(Refund).filter_by(razorpay_refund_id=r_data["id"])).scalar_one_or_none()
                    if not refund_obj:
                        r_amount = Decimal(r_data["amount"]) / 100
                        r_status = RefundStatus.PROCESSED.value if r_data["status"] == "processed" else RefundStatus.PENDING.value
                        refund_obj = Refund(
                            razorpay_refund_id=r_data["id"],
                            payment_id=payment_obj.id,
                            amount=r_amount,
                            status=r_status,
                            created_at=datetime.fromtimestamp(r_data["created_at"])
                        )
                        db.add(refund_obj)
                        db.flush()
                        stats["refunds_created"] += 1
            except Exception as e:
                logger.warning(f"Failed to fetch refunds for {p_data['id']}: {e}")

    existing_settlements = db.execute(select(Settlement)).scalars().all()
    if existing_settlements:
        return stats

    seed_now = datetime.now()
    today = seed_now.date()
    captured_payments = [p for p in inserted_payments if p.status == PaymentStatus.CAPTURED.value]

    synthetic_specs = {
        "delayed": ("pay_synth_delayed", Decimal("12000.00"), Decimal("120.00")),
        "partial": ("pay_synth_partial", Decimal("15000.00"), Decimal("150.00")),
        "duplicate": ("pay_synth_duplicate", Decimal("18000.00"), Decimal("180.00")),
        "fee_mismatch": ("pay_synth_fee_mismatch", Decimal("22000.00"), Decimal("220.00")),
        "bank_mismatch": ("pay_synth_bank_mismatch", Decimal("26000.00"), Decimal("260.00")),
    }
    clean_specs = [
        (f"pay_synth_clean_{index:02d}", Decimal(str(8000 + index * 1000)), Decimal("80.00"))
        for index in range(1, 11)
    ]

    def ensure_synthetic_payment(payment_id, amount, fee, created_at):
        order_id = f"synth_ord_{payment_id.removeprefix('pay_')}"
        order_obj = db.execute(select(Order).filter_by(razorpay_order_id=order_id)).scalar_one_or_none()
        if order_obj is None:
            order_obj = Order(
                razorpay_order_id=order_id,
                amount=amount,
                currency="INR",
                status=OrderStatus.PAID,
                created_at=created_at,
            )
            db.add(order_obj)
            db.flush()
            stats["orders_created"] += 1

        payment_obj = db.execute(select(Payment).filter_by(razorpay_payment_id=payment_id)).scalar_one_or_none()
        if payment_obj is None:
            payment_obj = Payment(
                razorpay_payment_id=payment_id,
                order_id=order_obj.id,
                amount=amount,
                fee=fee,
                tax=Decimal("0.00"),
                status=PaymentStatus.CAPTURED,
                method="card",
                created_at=created_at,
            )
            db.add(payment_obj)
            db.flush()
            stats["payments_created"] += 1

        fee_parts = ((FeeType.GATEWAY_FEE, fee), (FeeType.GST, Decimal("0.00")))
        for fee_type, fee_amount in fee_parts:
            existing_fee = db.execute(
                select(Fee).filter_by(payment_id=payment_obj.id, type=fee_type)
            ).scalar_one_or_none()
            if existing_fee is None:
                db.add(Fee(payment_id=payment_obj.id, type=fee_type, amount=fee_amount))
                stats["fees_created"] += 1
        db.flush()
        return payment_obj

    def create_settlement_for_payment(payment, settlement_type="clean"):
        expected_amount = payment.amount - payment.fee
        
        if settlement_type == "missing":
            return
            
        settlement_status = SettlementStatus.PROCESSED
        expected_date = today
        processed_date = today
        
        if settlement_type == "delayed":
            settlement_status = SettlementStatus.PROCESSING
            expected_date = today - timedelta(days=2)
            processed_date = None
        elif settlement_type == "on_hold":
            settlement_status = SettlementStatus.ON_HOLD
            
        s = Settlement(
            razorpay_settlement_id=f"set_{random.randint(10000000, 99999999)}",
            amount=expected_amount,
            status=settlement_status,
            expected_date=expected_date,
            processed_date=processed_date
        )
        db.add(s)
        db.flush()
        stats["settlements_created"] += 1
        
        si_amount = expected_amount
        if settlement_type == "partial":
            si_amount = expected_amount - Decimal('100.00')
            
        si = SettlementItem(
            settlement_id=s.id,
            payment_id=payment.id,
            amount=si_amount if settlement_type == "partial" else payment.amount,
            entry_type=SettlementItemEntryType.PAYMENT
        )
        db.add(si)
        
        if payment.fee > 0:
            fee_amount = payment.fee
            if settlement_type == "fee_mismatch":
                fee_amount = payment.fee - Decimal('10.00')
            
            sfi = SettlementItem(
                settlement_id=s.id,
                payment_id=payment.id,
                amount=-fee_amount,
                entry_type=SettlementItemEntryType.FEE_DEDUCTION
            )
            db.add(sfi)
        
        if settlement_type == "duplicate":
            si2 = SettlementItem(
                settlement_id=s.id,
                payment_id=payment.id,
                amount=payment.amount,
                entry_type=SettlementItemEntryType.PAYMENT
            )
            db.add(si2)
            s.amount = s.amount + payment.amount

        if settlement_type == "partial":
            s.amount = si_amount
            
        db.flush()
        stats["settlement_items_created"] += 2 if payment.fee > 0 or settlement_type == "duplicate" else 1

        if settlement_status == SettlementStatus.PROCESSED:
            bank_amount = s.amount
            if settlement_type == "bank_mismatch":
                bank_amount = s.amount - Decimal('50.00')
                
            bt = BankTransaction(
                settlement_id=s.id,
                amount=bank_amount,
                credited_date=today,
                bank_reference=f"UTR{random.randint(10000000000, 99999999999)}"
            )
            db.add(bt)
            stats["bank_transactions_created"] += 1

    missing_payment = db.execute(select(Payment).filter_by(razorpay_payment_id="pay_miss_50k")).scalar_one_or_none()
    if not missing_payment:
        missing_payment = ensure_synthetic_payment(
            "pay_miss_50k",
            Decimal("50000.00"),
            Decimal("0.00"),
            datetime.now() - timedelta(days=3),
        )
    captured_payments = [missing_payment] + [
        payment for payment in captured_payments if payment.id != missing_payment.id
    ]

    anomaly_types = list(synthetic_specs)
    for anomaly_type in anomaly_types[len(captured_payments) - 1:]:
        payment_id, amount, fee = synthetic_specs[anomaly_type]
        captured_payments.append(
            ensure_synthetic_payment(
                payment_id,
                amount,
                fee,
                seed_now,
            )
        )

    target_demo_payment_count = 16
    for payment_id, amount, fee in clean_specs:
        if len(captured_payments) >= target_demo_payment_count:
            break
        captured_payments.append(
            ensure_synthetic_payment(
                payment_id,
                amount,
                fee,
                seed_now,
            )
        )

    for i, p in enumerate(captured_payments):
        if i == 0:
            create_settlement_for_payment(p, "missing")
        elif i <= len(anomaly_types):
            create_settlement_for_payment(p, anomaly_types[i - 1])
        else:
            create_settlement_for_payment(p, "clean")

    db.commit()
    return stats
