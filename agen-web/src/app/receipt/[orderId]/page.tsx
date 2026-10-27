'use client';

/** G11 · Biên nhận thanh toán (không phải hoá đơn GTGT): xem và in / lưu PDF. */
import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, CircleAlert, LoaderCircle, Printer } from 'lucide-react';
import { useAuthHydrated, useAuthStore } from '@/store/authStore';
import { getReceipt, type Receipt } from '@/lib/billingService';
import { track } from '@/lib/analytics';
import { apiErrorMessage } from '@/lib/apiError';

const utc = (s: string | null | undefined) => (s ? new Date(/(?:[zZ]|[+-]\d\d:\d\d)$/.test(s) ? s : `${s}Z`) : null);
const fmtDate = (s: string | null | undefined) => utc(s)?.toLocaleString('vi-VN', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' }) ?? '—';

export default function ReceiptPage() {
  const { orderId } = useParams<{ orderId: string }>();
  const router = useRouter();
  const hydrated = useAuthHydrated();
  const { isAuthenticated } = useAuthStore();
  const [r, setR] = useState<Receipt | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!hydrated) return;
    if (!isAuthenticated) { router.push('/login'); return; }
    getReceipt(orderId).then(x => { setR(x); track('receipt_opened', { provider: x.order.provider }); })
      .catch(err => setError(apiErrorMessage(err, 'Không tìm thấy biên nhận.')));
  }, [hydrated, isAuthenticated, router, orderId]);

  if (!r) {
    return <main className="report-page" style={{ display: 'grid', placeItems: 'center' }}>{error ? <div className="alert-error"><CircleAlert size={16} /> {error}</div> : <LoaderCircle className="animate-spin" size={22} />}</main>;
  }
  const o = r.order;
  const usd = o.currency === 'USD' && o.amount_foreign != null;
  const amount = usd ? `$${(o.amount_foreign! / 100).toFixed(2)} USD` : `${o.amount_vnd.toLocaleString('vi-VN')} ₫`;

  return (
    <main className="report-page">
      <div className="report-toolbar no-print">
        <Link href="/upgrade" style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}><ArrowLeft size={16} /> Gói của tôi</Link>
        <button type="button" className="btn btn-primary btn-sm" onClick={() => window.print()}><Printer size={14} /> In / Lưu PDF</button>
      </div>
      <article className="report-sheet receipt-sheet" data-refunded={o.status === 'refunded'}>
        <div className="report-head">
          <div>
            <div className="eyebrow">Biên nhận thanh toán · Payment receipt</div>
            <h1 className="report-title" style={{ fontSize: '1.6rem' }}>{r.number}</h1>
          </div>
          <div style={{ textAlign: 'right', fontSize: '0.85rem', color: '#515154' }}>
            <strong style={{ color: '#1D1D1F' }}>{r.seller.name}</strong>
            {r.seller.tax_code && <div>MST: {r.seller.tax_code}</div>}
            {r.seller.address && <div>{r.seller.address}</div>}
            {r.seller.email && <div>{r.seller.email}</div>}
          </div>
        </div>
        {o.status === 'refunded' && <div className="receipt-refunded">ĐÃ HOÀN TIỀN {o.refunded_at ? `· ${fmtDate(o.refunded_at)}` : ''}{r.refund_note ? ` · ${r.refund_note}` : ''}</div>}
        <div className="receipt-grid">
          <div><span>Người mua</span><strong>{r.buyer.name || '—'}</strong><div>{r.buyer.email}</div></div>
          <div><span>Ngày thanh toán</span><strong>{fmtDate(o.paid_at)}</strong><div>Mã đơn {o.order_id.slice(0, 8).toUpperCase()}</div></div>
          <div><span>Hình thức</span><strong>{r.provider_label}</strong>{r.provider_txn && <div>Mã giao dịch {r.provider_txn}</div>}</div>
        </div>
        <table className="receipt-table">
          <thead><tr><th>Nội dung</th><th style={{ textAlign: 'right' }}>Số tiền</th></tr></thead>
          <tbody>
            <tr><td>{r.item}</td><td style={{ textAlign: 'right' }}>{amount}</td></tr>
          </tbody>
          <tfoot><tr><td>Tổng đã thanh toán</td><td style={{ textAlign: 'right' }}>{amount}</td></tr></tfoot>
        </table>
        {usd && <p className="receipt-note">Quy đổi nội bộ để thống kê: {o.amount_vnd.toLocaleString('vi-VN')} ₫.</p>}
        {r.invoice && (
          <div className="receipt-note">
            Thông tin xuất hoá đơn GTGT: <b>{r.invoice.company_name}</b> · MST {r.invoice.tax_code} · {r.invoice.address} · {r.invoice.email}
            {o.invoice_issued_at ? ' — hoá đơn điện tử đã được gửi.' : ' — hoá đơn điện tử sẽ được gửi qua email.'}
          </div>
        )}
        {r.einvoice ? (
          <div className="receipt-note" style={{ color: '#1D1D1F' }}>
            Hoá đơn điện tử đã xuất: số <b>{r.einvoice.number}</b>{r.einvoice.series ? ` · ký hiệu ${r.einvoice.series}` : ''}
            {r.einvoice.lookup_code && <> · mã tra cứu <b>{r.einvoice.lookup_code}</b></>}
            {r.einvoice.lookup_url && <> · tra cứu tại <a href={r.einvoice.lookup_url} target="_blank" rel="noreferrer">{r.einvoice.lookup_url}</a></>}
            {r.einvoice.seller_tax_code && <> (MST người bán {r.einvoice.seller_tax_code})</>}.
          </div>
        ) : null}
        <p className="receipt-note">Biên nhận này xác nhận khoản thanh toán, không thay thế hoá đơn giá trị gia tăng.</p>
      </article>
    </main>
  );
}
