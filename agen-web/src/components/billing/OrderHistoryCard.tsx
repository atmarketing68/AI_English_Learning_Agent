'use client';

/** G11 · Lịch sử thanh toán của tài khoản, có link biên nhận in được. */
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Receipt as ReceiptIcon } from 'lucide-react';
import { getMyOrders, type OrderInfo } from '@/lib/billingService';

const PLAN_VI: Record<string, string> = { premium: 'Premium', family: 'Gia đình', team: 'Theo ghế' };
const STATUS_VI: Record<string, string> = { paid: 'Đã thanh toán', refunded: 'Đã hoàn tiền', pending: 'Chờ thanh toán', failed: 'Không thành công' };

export default function OrderHistoryCard() {
  const [orders, setOrders] = useState<OrderInfo[] | null>(null);
  useEffect(() => { getMyOrders().then(setOrders).catch(() => setOrders([])); }, []);
  const shown = (orders ?? []).filter(o => o.status === 'paid' || o.status === 'refunded');
  if (!shown.length) return null;
  return (
    <section className="card" style={{ marginTop: 'var(--spacing-xl)' }}>
      <div className="section-head"><h3><ReceiptIcon size={16} /> Lịch sử thanh toán</h3></div>
      {shown.map(o => (
        <div key={o.order_id} className="member-cert" style={{ justifyContent: 'space-between' }}>
          <span style={{ minWidth: 0 }}>
            <b>{PLAN_VI[o.plan] ?? o.plan} · {o.months} tháng</b>
            <br /><small style={{ color: 'var(--text-muted)' }}>
              {o.paid_at ? new Date(o.paid_at.endsWith('Z') ? o.paid_at : `${o.paid_at}Z`).toLocaleDateString('vi-VN') : ''} ·{' '}
              {o.currency === 'USD' && o.amount_foreign != null ? `$${(o.amount_foreign / 100).toFixed(2)}` : `${o.amount_vnd.toLocaleString('vi-VN')} ₫`} · {STATUS_VI[o.status]}
            </small>
          </span>
          <Link href={`/receipt/${o.order_id}`} className="btn btn-ghost btn-sm">Biên nhận</Link>
        </div>
      ))}
    </section>
  );
}
