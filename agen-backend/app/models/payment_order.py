"""G3 · Thanh toán thật — one row per checkout attempt (VNPay / MoMo)."""
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String

from app.core.database import Base

STATUS_PENDING = "pending"
STATUS_PAID = "paid"
STATUS_FAILED = "failed"


class PaymentOrder(Base):
    __tablename__ = "payment_orders"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)

    provider = Column(String(20), nullable=False)            # vnpay | momo
    plan = Column(String(20), nullable=False, default="premium", server_default="premium")   # premium | family (G5)
    months = Column(Integer, nullable=False)
    seats = Column(Integer, nullable=False, default=1, server_default="1")      # G7 · team plan seats
    amount_vnd = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False, default=STATUS_PENDING)

    # Provider-side identifiers (transaction no, pay URL) and the raw callback.
    provider_txn = Column(String(120), nullable=True)
    pay_url = Column(String(2000), nullable=True)
    callback = Column(JSON, nullable=True)

    # G8 · hoá đơn VAT cho doanh nghiệp: {company_name, tax_code, address, email}; set when the buyer asks for one.
    invoice_info = Column(JSON, nullable=True)
    invoice_issued_at = Column(DateTime, nullable=True)       # admin marks the e-invoice as sent

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    paid_at = Column(DateTime, nullable=True)
