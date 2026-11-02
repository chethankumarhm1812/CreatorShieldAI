import { FormEvent, useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { FileText, CheckCircle2, CalendarDays, ShieldCheck, ArrowRight, RefreshCw } from 'lucide-react';
import { addCreatorAccount, bindPolicy, creatorAccounts, policies, quote } from '../services/api';
import { Card, Badge } from '../components/UI';

const money = (amount: number) => `₹${Number(amount || 0).toLocaleString('en-IN')}`;

export default function Policy() {
  const [policyRows, setPolicyRows] = useState<any[]>([]);
  const [accounts, setAccounts] = useState<any[]>([]);
  const [quoteResult, setQuoteResult] = useState<any>();
  const [quoteInput, setQuoteInput] = useState({ requested_limit: 150000, platform: 'YouTube' });
  const [accountInput, setAccountInput] = useState({ platform: 'YouTube', handle: '', monetized: true });
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [accountBusy, setAccountBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const refresh = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const [policyData, accountData] = await Promise.all([policies(), creatorAccounts()]);
      setPolicyRows(policyData);
      setAccounts(accountData);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Policies could not be loaded.');
    } finally {
      setLoading(false);
    }
  }, []);
  useEffect(() => { void refresh(); }, [refresh]);

  async function runQuote() {
    setBusy(true);
    setError('');
    setNotice('');
    try {
      setQuoteResult(await quote(quoteInput));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Quote could not be calculated.');
    } finally {
      setBusy(false);
    }
  }

  async function bind() {
    setBusy(true);
    setError('');
    try {
      const result = await bindPolicy(quoteInput);
      setNotice(`Policy ${result.policy.number} is bound. Pay invoice ${result.invoice_number} to activate coverage.`);
      setQuoteResult(undefined);
      await refresh();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Policy could not be bound.');
    } finally {
      setBusy(false);
    }
  }

  async function addAccount(event: FormEvent) {
    event.preventDefault();
    setAccountBusy(true);
    setError('');
    setNotice('');
    try {
      const account = await addCreatorAccount(accountInput);
      setNotice(`${account.platform} account ${account.handle} added. Security score: ${account.security_score}/100.`);
      setAccountInput({ ...accountInput, handle: '' });
      await refresh();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Digital account could not be added.');
    } finally {
      setAccountBusy(false);
    }
  }

  const policy = policyRows[0];
  return <>
    <div className="page-head"><div><span className="eyebrow">POLICYCENTER SIMULATOR</span><h2>Policy administration</h2><p>Product, quote, underwriting and policy lifecycle in one model.</p></div></div>
    {error && <Card className="inline-alert"><b>Action could not be completed</b><p>{error}</p><button className="ghost" onClick={() => void refresh()}><RefreshCw size={15}/> Retry</button></Card>}
    {notice && <div className="success">{notice} <Link to="/billing">Go to billing <ArrowRight size={14}/></Link></div>}
    <Card className="account-card"><div className="section-title"><div><span className="eyebrow">CREATOR PROFILE</span><h3>Connected digital accounts</h3></div></div>
      {accounts.length ? <div className="account-list">{accounts.map((account: any) => <div className="account-row" key={account.id}><div><b>{account.platform} · {account.handle}</b><span>{account.monetized ? 'Monetized account' : 'Non-monetized account'}</span></div><div><Badge>{account.security_score}/100 SECURITY</Badge></div></div>)}</div> : <div className="empty compact-empty">Add the creator account you want to protect.</div>}
      <form className="account-form" onSubmit={addAccount}><label>Platform<select value={accountInput.platform} onChange={(event) => setAccountInput({ ...accountInput, platform: event.target.value })}><option>YouTube</option><option>Instagram</option><option>TikTok</option><option>Twitch</option><option>Other</option></select></label><label>Handle<input value={accountInput.handle} onChange={(event) => setAccountInput({ ...accountInput, handle: event.target.value })} minLength={2} required placeholder="@yourchannel"/></label><label className="checkbox-label"><input type="checkbox" checked={accountInput.monetized} onChange={(event) => setAccountInput({ ...accountInput, monetized: event.target.checked })}/> Monetized</label><button className="secondary" disabled={accountBusy}>{accountBusy ? 'Adding…' : 'Add account'}</button></form>
    </Card>
    <div className="form-grid policy-quote-grid">
      <Card><div className="section-title"><div><span className="eyebrow">PRODUCT & UNDERWRITING</span><h3>Creator Digital Asset Protection</h3></div><Badge>SIMULATOR</Badge></div>
        <form className="form" onSubmit={(event) => { event.preventDefault(); void runQuote(); }}>
          <label>Choose a coverage limit<select value={quoteInput.requested_limit} onChange={(event) => setQuoteInput({ ...quoteInput, requested_limit: Number(event.target.value) })}><option value={100000}>{money(100000)} — Starter</option><option value={150000}>{money(150000)} — Standard</option><option value={200000}>{money(200000)} — Plus</option><option value={250000}>{money(250000)} — Underwriter review</option><option value={350000}>{money(350000)} — Above simulator maximum</option></select></label>
          <label>Primary creator platform<select value={quoteInput.platform} onChange={(event) => setQuoteInput({ ...quoteInput, platform: event.target.value })}><option>YouTube</option><option>Instagram</option><option>TikTok</option><option>Twitch</option><option>Other</option></select></label>
          <button className="primary" disabled={busy}>{busy ? 'Calculating…' : 'Calculate quote'} <ArrowRight size={16}/></button>
        </form>
      </Card>
      <Card>{quoteResult ? <><div className="section-title"><div><span className="eyebrow">QUOTE RESULT</span><h3>{money(quoteResult.premium)} / year</h3></div><Badge>{quoteResult.underwriting}</Badge></div><div className="detail-grid"><div><span>Requested limit</span><b>{money(quoteResult.requested_limit)}</b></div><div><span>Security score</span><b>{quoteResult.security_score}/100</b></div></div><p className="large-copy">{quoteResult.reason}</p>{quoteResult.underwriting === 'STANDARD' && <button className="primary" disabled={busy} onClick={() => void bind()}>Select this policy & create invoice <ArrowRight size={16}/></button>}</> : <div className="empty"><FileText size={32}/><h3>Choose a policy limit</h3><p>Select a coverage limit and calculate your quote. Security score affects the indicative premium, but does not block standard policies up to ₹200,000.</p></div>}</Card>
    </div>
    {loading ? <div className="loading">Loading policies…</div> : policyRows.length === 0 ? <Card className="empty"><ShieldCheck size={34}/><h3>No policies yet</h3><p>Run a quote above and bind an eligible policy to create your BillingCenter account and first invoice.</p></Card> : policyRows.map((p) => <div key={p.id} className="grid2">
      <Card><div className="policy-hero"><div className="policy-icon"><ShieldCheck/></div><div><span className="eyebrow">{p.number}</span><h3>{p.product}</h3><Badge>{p.status}</Badge></div></div><div className="detail-grid"><div><span>Effective</span><b>{p.effective}</b></div><div><span>Expiry</span><b>{p.expiry}</b></div><div><span>Annual premium</span><b>{money(p.premium)}</b></div><div><span>Deductible</span><b>{money(p.deductible)}</b></div></div>{p.status === 'BOUND' && <p className="warning-copy">Coverage is not active until the first premium invoice is paid. <Link to="/billing">Pay invoice</Link></p>}</Card>
      <Card><div className="section-title"><div><span className="eyebrow">COVERAGES</span><h3>Protection stack</h3></div></div>{p.coverages.map((coverage: any) => <div className="coverage-row" key={coverage.code}><div><b>{coverage.name}</b><span>{coverage.daily_benefit ? `${money(coverage.daily_benefit)}/day benefit` : coverage.code}</span></div><strong>{money(coverage.limit)}</strong></div>)}</Card>
      <Card className="lifecycle-card"><div className="section-title"><div><span className="eyebrow">POLICY LIFECYCLE</span><h3>Quote → bind → issue → renew</h3></div></div><div className="lifecycle">{[['Quote', 'Risk evaluated'], ['Bind', 'Terms accepted'], ['Issue', p.status === 'ACTIVE' ? 'Coverage active' : 'Awaiting premium'], ['Renew', p.expiry]].map(([name, description], index) => <div className={index < (p.status === 'ACTIVE' ? 3 : 2) ? 'active' : ''} key={name}>{index < (p.status === 'ACTIVE' ? 3 : 2) ? <CheckCircle2/> : <CalendarDays/>}<b>{name}</b><span>{description}</span></div>)}</div></Card>
    </div>)}
  </>;
}
