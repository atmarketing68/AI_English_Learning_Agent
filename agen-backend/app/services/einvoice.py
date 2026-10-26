"""
G12 · Hoá đơn điện tử qua Viettel S-Invoice.

Follows the integration Odoo ships for Viettel (l10n_vn_edi_viettel):
  login   POST {VIETTEL_SINVOICE_LOGIN_URL} {"username","password"} → {"access_token","expires_in"}
  create  POST {API}/InvoiceAPI/InvoiceWS/createInvoice/{sellerTaxCode}, token sent as cookie "access_token"
  result  {"result": {"invoiceNo", "reservationCode"}}; errors come back as "code"/"error" (or "errorCode").
Amounts are what the buyer paid (tax included); with EINVOICE_TAX_PERCENT > 0 the net price and VAT
are split out, -2 means "không chịu thuế". The transaction UUID is stored before calling Viettel and
re-used on a retry so a timeout cannot create a second invoice. Off until fully configured.
"""
from __future__ import annotations

import logging
import time
import uuid
from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.payment_order import STATUS_PAID, PaymentOrder
from app.models.user import User

logger = logging.getLogger("agen.einvoice")
TIMEOUT_S = 60
_token: dict = {"value": None, "expires": 0.0}


class EInvoiceError(RuntimeError):
    pass


def seller_tax_code() -> str:
    return (settings.VIETTEL_SINVOICE_TAX_CODE or settings.SELLER_TAX_CODE or "").strip()


def enabled() -> bool:
    return (settings.EINVOICE_PROVIDER or "").lower() == "viettel" and all([
        settings.VIETTEL_SINVOICE_USERNAME, settings.VIETTEL_SINVOICE_PASSWORD, seller_tax_code(),
        settings.VIETTEL_SINVOICE_TEMPLATE_CODE, settings.VIETTEL_SINVOICE_SERIES])


def _login() -> str:
    if _token["value"] and _token["expires"] > time.time() + 60:
        return _token["value"]
    try:
        resp = httpx.post(settings.VIETTEL_SINVOICE_LOGIN_URL, json={"username": settings.VIETTEL_SINVOICE_USERNAME,
                                                                     "password": settings.VIETTEL_SINVOICE_PASSWORD}, timeout=TIMEOUT_S)
        data = resp.json()
    except Exception as exc:
        raise EInvoiceError(f"Không đăng nhập được Viettel S-Invoice: {exc}") from exc
    token = data.get("access_token") if isinstance(data, dict) else None
    if resp.status_code >= 400 or not token:
        raise EInvoiceError(f"Viettel từ chối đăng nhập: {(data or {}).get('error_description') or (data or {}).get('error') or resp.status_code}")
    _token.update(value=token, expires=time.time() + float(data.get("expires_in") or 600))
    return token


def split_amount(total_vnd: int, tax_percent: int) -> tuple[int, int]:
    """Tax-inclusive total → (net, tax). Non-positive tax percents (KCT/KKKNT) carry no tax."""
    if tax_percent <= 0:
        return total_vnd, 0
    net = round(total_vnd * 100 / (100 + tax_percent))
    return net, total_vnd - net


def build_payload(order: PaymentOrder, buyer: User | None, txn: str, issued_at: datetime) -> dict:
    plan_vi = {"premium": "Premium", "family": "Gói gia đình", "team": "Gói theo ghế"}.get(order.plan or "premium", order.plan or "Premium")
    item_name = f"Dịch vụ học tiếng Anh trực tuyến AI AGENT ENGLISH – {plan_vi} {order.months} tháng" + (f", {order.seats} ghế" if order.plan == "team" else "")
    tax_percent = int(settings.EINVOICE_TAX_PERCENT)
    net, tax = split_amount(int(order.amount_vnd or 0), tax_percent)
    inv = order.invoice_info if isinstance(order.invoice_info, dict) else None
    buyer_name = (getattr(buyer, "full_name", None) or getattr(buyer, "email", None) or "Khách hàng").strip()[:200]
    buyer_info = {
        "buyerName": buyer_name,
        "buyerLegalName": (inv or {}).get("company_name", "")[:400],
        "buyerTaxCode": (inv or {}).get("tax_code", ""),
        "buyerAddressLine": (inv or {}).get("address", ""),
        "buyerEmail": (inv or {}).get("email") or getattr(buyer, "email", "") or "",
        "buyerNotGetInvoice": 0,
    }
    seller = {"sellerLegalName": settings.SELLER_NAME, "sellerTaxCode": seller_tax_code()}
    if settings.SELLER_ADDRESS:
        seller["sellerAddressLine"] = settings.SELLER_ADDRESS
    if settings.SELLER_EMAIL:
        seller["sellerEmail"] = settings.SELLER_EMAIL
    return {
        "generalInvoiceInfo": {
            "transactionUuid": txn,
            "invoiceType": settings.VIETTEL_SINVOICE_INVOICE_TYPE,
            "templateCode": settings.VIETTEL_SINVOICE_TEMPLATE_CODE,
            "invoiceSeries": settings.VIETTEL_SINVOICE_SERIES,
            "invoiceIssuedDate": int(issued_at.replace(tzinfo=timezone.utc).timestamp()) * 1000,
            "currencyCode": "VND",
            "adjustmentType": "1",
            "paymentStatus": True,
            "cusGetInvoiceRight": True,
            "validation": 1,
        },
        "buyerInfo": buyer_info,
        "sellerInfo": seller,
        "payments": [{"paymentMethodName": "TM/CK"}],
        "itemInfo": [{
            "lineNumber": 1, "selection": 1, "itemCode": (order.plan or "premium").upper(), "itemName": item_name[:500],
            "unitName": settings.EINVOICE_UNIT_NAME, "unitPrice": net, "quantity": 1, "discount": 0,
            "itemTotalAmountWithoutTax": net, "taxPercentage": tax_percent, "taxAmount": tax,
            "itemTotalAmountAfterDiscount": net, "itemTotalAmountWithTax": net + tax,
        }],
        "taxBreakdowns": [{"taxPercentage": tax_percent, "taxableAmount": net, "taxAmount": tax, "taxableAmountPos": True, "taxAmountPos": True}],
    }


def issue(db: Session, order: PaymentOrder) -> PaymentOrder:
    """Create the e-invoice for a paid order (caller commits). Raises EInvoiceError; the error is also kept on the order."""
    if not enabled():
        raise EInvoiceError("Chưa cấu hình hoá đơn điện tử Viettel.")
    if order.status != STATUS_PAID:
        raise EInvoiceError("Chỉ xuất hoá đơn cho đơn đã thanh toán.")
    if order.einvoice_no:
        raise EInvoiceError(f"Đơn này đã có hoá đơn số {order.einvoice_no}.")
    if not order.einvoice_txn:
        order.einvoice_txn = str(uuid.uuid4())
        db.commit()                       # keep the id even if the call below times out → a retry re-uses it
    buyer = db.query(User).filter(User.id == order.user_id).first()
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    payload = build_payload(order, buyer, order.einvoice_txn, now)
    url = f"{settings.VIETTEL_SINVOICE_API_URL.rstrip('/')}/InvoiceAPI/InvoiceWS/createInvoice/{seller_tax_code()}"
    try:
        resp = httpx.post(url, json=payload, cookies={"access_token": _login()}, timeout=TIMEOUT_S)
        data = resp.json()
    except EInvoiceError as exc:
        order.einvoice_error = str(exc)[:300]
        raise
    except Exception as exc:
        order.einvoice_error = f"Viettel không phản hồi: {exc}"[:300]
        raise EInvoiceError(order.einvoice_error) from exc
    data = data if isinstance(data, dict) else {}
    err = data.get("code") or data.get("error") or data.get("errorCode")
    result = data.get("result") or {}
    if resp.status_code >= 400 or err or not result.get("invoiceNo"):
        message = data.get("data") or data.get("description") or data.get("message") or data.get("error") or resp.status_code
        order.einvoice_error = f"Viettel từ chối: {message}"[:300]
        raise EInvoiceError(order.einvoice_error)
    order.einvoice_no = str(result["invoiceNo"])[:40]
    order.einvoice_lookup_code = (str(result.get("reservationCode") or "")[:60]) or None
    order.einvoice_error = None
    order.invoice_issued_at = now
    return order


def run_auto(db: Session, now: datetime | None = None, limit: int = 10) -> dict:
    """Hourly cron: issue e-invoices for recent paid orders when EINVOICE_AUTO is business/all. Never raises."""
    mode = (settings.EINVOICE_AUTO or "off").lower()
    if mode not in ("business", "all") or not enabled():
        return {"enabled": False}
    now = now or datetime.now(timezone.utc).replace(tzinfo=None)
    q = db.query(PaymentOrder).filter(PaymentOrder.status == STATUS_PAID, PaymentOrder.einvoice_no.is_(None),
                                      PaymentOrder.provider != "demo", PaymentOrder.paid_at >= now - timedelta(days=3))
    if mode == "business":
        q = q.filter(PaymentOrder.invoice_info.isnot(None))
    out = {"enabled": True, "issued": 0, "failed": 0}
    for order in q.order_by(PaymentOrder.paid_at).limit(limit).all():
        try:
            issue(db, order)
            db.commit()
            out["issued"] += 1
        except Exception:
            db.commit()                    # keep the error text on the order for the admin
            out["failed"] += 1
            logger.warning("Auto e-invoice failed for order %s", order.id, exc_info=True)
    return out
