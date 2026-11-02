import { useCallback, useEffect, useState } from 'react';
import { CheckCircle2, Receipt, WalletCards, RefreshCw, CreditCard } from 'lucide-react';
import { billing, payInvoice } from '../services/api';
import { Card, Badge, Stat } from '../components/UI';

const money = (amount: number) => `₹${Number(amount || 0).toLocaleString('en-IN')}`;

export default function Billing() {
  const [accounts, setAccounts] = useState<any[]>([]);
  const [busy, setBusy] = useState<number | null>(null);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [loading, setLoading] = useState(true);
  const isCreator = JSON.parse(localStorage.getItem('user') || 'null')?.role === 'CREATOR';
  const refresh = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      setAccounts(await billing());
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Billing data could not be loaded.');
    } finally {
      setLoading(false);
    }
  }, []);
  useEffect(() => { void refresh(); }, [refresh]);

  async function pay(id: number) {
    setBusy(id);
    setError('');
    setNotice('');
    try {
      const result = await payInvoice(id);
      setNotice(`Payment ${result.payment_reference} recorded. Policy status: ${result.policy_status}.`);
      await refresh();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Payment could not be recorded.');
    } finally {
      setBusy(null);
    }
  }

  if (loading) return <div className="loading">Loading billing accounts…</div>;
  const first = accounts[0];
  return <>
    <div className="page-head"><div><span className="eyebrow">BILLINGCENTER SIMULATOR</span><h2>Premium & payments</h2><p>Billing account, invoices and payment lifecycle.</p></div><button className="secondary" onClick={() => void refresh()}><RefreshCw size={15}/> Refresh</button></div>
    {error && <Card className="inline-alert"><b>Billing action failed</b><p>{error}</p></Card>}
    {notice && <div className="success">{notice}</div>}
    {!first ? <Card className="empty"><WalletCards size={36}/><h3>No billing account</h3><p>Bind a standard policy quote to create an invoice and billing account.</p></Card> : <>
      <div className="stats"><Stat label="Billing account" value={first.account_number} sub={first.status} icon={<WalletCards/>}/><Stat label="Outstanding" value={money(first.outstanding)} sub={first.outstanding ? 'Payment required' : 'No balance due'} icon={<Receipt/>}/><Stat label="Next due" value={first.next_due || '—'} sub="Scheduled invoice" icon={<CheckCircle2/>}/><Stat label="Invoices" value={accounts.reduce((count, account) => count + account.invoices.length, 0)} sub="Billing history" icon={<CreditCard/>}/></div>
      {accounts.map((account: any) => <Card key={account.account_number} className="billing-card"><div className="section-title"><div><span className="eyebrow">BILLING ACCOUNT · {account.account_number}</span><h3>Invoice history</h3></div><Badge>{account.status}</Badge></div>
        {account.invoices.length === 0 ? <div className="empty">No invoices have been generated for this account.</div> : <div className="table-scroll"><table><thead><tr><th>Invoice</th><th>Due date</th><th>Amount</th><th>Status</th><th>Payment</th></tr></thead><tbody>{account.invoices.map((invoice: any) => <tr key={invoice.id}><td><b>{invoice.number}</b></td><td>{invoice.due}</td><td>{money(invoice.amount)}</td><td><Badge>{invoice.status}</Badge></td><td>{invoice.status === 'PAID' ? <span className="payment-ref">{invoice.payments?.[0]?.reference || 'Paid'}</span> : isCreator ? <button className="primary small" disabled={busy === invoice.id} onClick={() => void pay(invoice.id)}>{busy === invoice.id ? 'Processing…' : 'Pay premium'}</button> : <span>Awaiting creator payment</span>}</td></tr>)}</tbody></table></div>}
        {account.invoices.some((invoice: any) => invoice.payments?.length) && <div className="payment-history"><b>Payment history</b>{account.invoices.flatMap((invoice: any) => invoice.payments.map((payment: any) => <div className="payment-row" key={payment.reference}><span>{payment.reference}</span><span>{payment.date ? new Date(payment.date).toLocaleString() : '—'}</span><Badge>{payment.status}</Badge><strong>{money(payment.amount)}</strong></div>))}</div>}
      </Card>)}
      <p className="disclaimer">Payment actions are simulated locally and do not charge a real payment method.</p>
    </>}
  </>;
}
