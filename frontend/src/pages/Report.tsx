import { FormEvent, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ShieldAlert, ArrowRight } from 'lucide-react';
import { submitFNOL } from '../services/api';
import { Card } from '../components/UI';

const localDate = () => {
  const date = new Date();
  date.setMinutes(date.getMinutes() - date.getTimezoneOffset());
  return date.toISOString().slice(0, 10);
};

export default function Report() {
  const [type, setType] = useState('ACCOUNT_TAKEOVER');
  const [platform, setPlatform] = useState('YouTube');
  const [date, setDate] = useState(localDate());
  const [restored, setRestored] = useState('');
  const [description, setDescription] = useState('');
  const [recoveryExpense, setRecoveryExpense] = useState(30000);
  const [legalExpense, setLegalExpense] = useState(10000);
  const [revenueLoss, setRevenueLoss] = useState(25000);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError('');
    if (restored && restored < date) {
      setError('Restoration date cannot be earlier than the incident date.');
      return;
    }
    if (!recoveryExpense && !legalExpense && !revenueLoss) {
      setError('Enter at least one claimed expense or revenue loss.');
      return;
    }
    setBusy(true);
    try {
      await submitFNOL({
        incident_type: type,
        platform,
        occurred_on: date,
        restored_on: restored || null,
        description,
        recovery_expense: type === 'COVERED_RESTRICTION' ? 0 : recoveryExpense,
        legal_expense: type === 'COVERED_RESTRICTION' ? 0 : legalExpense,
        revenue_loss: revenueLoss,
      });
      navigate('/claims');
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'FNOL could not be submitted.');
    } finally {
      setBusy(false);
    }
  }

  const restriction = type === 'COVERED_RESTRICTION';
  return <>
    <div className="page-head"><div><span className="eyebrow">FIRST NOTICE OF LOSS · CLAIMCENTER SIMULATOR</span><h2>Report an incident</h2><p>Tell us what happened and provide your initial claimed loss. An adjuster will verify eligibility and evidence.</p></div></div>
    <div className="form-grid">
      <Card><form onSubmit={submit} className="form">
        <label>Incident type<select value={type} onChange={(event) => setType(event.target.value)}><option value="ACCOUNT_TAKEOVER">Account takeover</option><option value="MALWARE_COMPROMISE">Malware compromise</option><option value="RANSOMWARE">Ransomware</option><option value="COVERED_RESTRICTION">Covered account restriction</option></select></label>
        <label>Affected platform<select value={platform} onChange={(event) => setPlatform(event.target.value)}><option>YouTube</option><option>Instagram</option><option>TikTok</option><option>Twitch</option><option>Other</option></select></label>
        <label>Incident date<input type="date" value={date} max={localDate()} onChange={(event) => setDate(event.target.value)} required/></label>
        <label>Account restored (optional)<input type="date" value={restored} min={date} max={localDate()} onChange={(event) => setRestored(event.target.value)}/></label>
        {!restriction && <><label>Recovery / technical expense (₹)<input type="number" min="0" max="500000" step="1" value={recoveryExpense} onChange={(event) => setRecoveryExpense(Number(event.target.value))}/></label><label>Legal expense (₹)<input type="number" min="0" max="500000" step="1" value={legalExpense} onChange={(event) => setLegalExpense(Number(event.target.value))}/></label></>}
        <label>Claimed revenue loss (₹)<input type="number" min="0" max="500000" step="1" value={revenueLoss} onChange={(event) => setRevenueLoss(Number(event.target.value))}/></label>
        <label>What happened?<textarea value={description} onChange={(event) => setDescription(event.target.value)} placeholder="Describe the incident, timeline and impact…" minLength={10} maxLength={3000} required/></label>
        {error && <div className="error">{error}</div>}
        <button className="primary" disabled={busy}>{busy ? 'Submitting FNOL…' : 'Create FNOL & claim'} <ArrowRight size={17}/></button>
      </form></Card>
      <Card><div className="incident-guide"><div className="guide-icon"><ShieldAlert/></div><h3>What happens next?</h3><div><b>01 · FNOL</b><span>Your incident and claimed exposures are registered in the ClaimCenter simulator.</span></div><div><b>02 · Evidence</b><span>Provide platform alerts, recovery records, legal invoices and verified revenue statements.</span></div><div><b>03 · Investigation</b><span>AI agents organize findings and surface inconsistencies; they do not decide coverage.</span></div><div><b>04 · Adjuster decision</b><span>Deterministic policy rules and a human adjuster determine the claim outcome.</span></div><p className="disclaimer">Claimed amounts are not approved benefits. Coverage limits, waiting periods, evidence verification and the policy deductible apply.</p></div></Card>
    </div>
  </>;
}
