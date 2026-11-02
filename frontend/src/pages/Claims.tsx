import { useCallback, useEffect, useMemo, useState } from 'react';
import { addEvidence, audit, claims as getClaims, investigate, assess, decide, pay, closeClaim, recordExclusion, verifyEvidence } from '../services/api';
import { Card, Badge, Stat } from '../components/UI';
import { BrainCircuit, FileCheck2, Scale, IndianRupee, History, RefreshCw, AlertTriangle, Upload, CheckCircle2 } from 'lucide-react';

const money = (amount: number) => `₹${Number(amount || 0).toLocaleString('en-IN')}`;
type Action = (id: number) => Promise<unknown>;

export default function Claims({ user }: { user: any }) {
  const [rows, setRows] = useState<any[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [auditRows, setAuditRows] = useState<any[] | null>(null);
  const isAdjuster = user.role === 'ADJUSTER';
  const selected = useMemo(() => rows.find((claim) => claim.id === selectedId), [rows, selectedId]);
  const canAddEvidence = selected && ['OPEN', 'INVESTIGATION', 'EVIDENCE_REQUIRED'].includes(selected.status);
  const canInvestigate = selected && ['OPEN', 'INITIAL_REVIEW', 'INVESTIGATION', 'EVIDENCE_REQUIRED', 'PENDING_APPROVAL'].includes(selected.status);
  const canAssess = selected && ['INVESTIGATION', 'EVIDENCE_REQUIRED', 'COVERAGE_REVIEW', 'PENDING_APPROVAL'].includes(selected.status);
  const finalized = selected && ['PAID', 'DENIED', 'CLOSED'].includes(selected.status);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const result = await getClaims();
      setRows(result);
      setSelectedId((current) => current && result.some((claim: any) => claim.id === current) ? current : result[0]?.id ?? null);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Claims could not be loaded.');
    } finally {
      setLoading(false);
    }
  }, []);
  useEffect(() => { void refresh(); }, [refresh]);

  async function run(action: Action, successMessage = 'Claim updated successfully.') {
    if (!selected) return;
    setBusy(true);
    setError('');
    setNotice('');
    try {
      await action(selected.id);
      setNotice(successMessage);
      await refresh();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'The claim action could not be completed.');
    } finally {
      setBusy(false);
    }
  }

  async function requestEvidence() {
    if (!selected) return;
    const type = window.prompt('Evidence type (for example, Revenue Statement):');
    if (!type) return;
    const file = window.prompt('Evidence file name or secure reference:');
    if (!file) return;
    const notes = window.prompt('Brief notes about this evidence:') || '';
    await run((id) => addEvidence(id, { evidence_type: type, file_name: file, notes }), 'Evidence reference added. An adjuster must verify it.');
  }

  async function manualDecision(decision: string) {
    if (!selected) return;
    const reason = window.prompt(`${decision === 'APPROVE' ? 'Approval' : decision === 'DENY' ? 'Denial' : 'Information request'} reason (required):`);
    if (!reason?.trim()) return;
    await run((id) => decide(id, decision, reason.trim()), `Adjuster decision recorded: ${decision.replace(/_/g, ' ')}.`);
  }

  async function verifyItem(evidenceId: number, verified: boolean) {
    const reason = window.prompt(`${verified ? 'Verification' : 'Rejection'} reason (required):`);
    if (!reason?.trim()) return;
    const item = selected?.evidence.find((evidence: any) => evidence.id === evidenceId);
    const financial = item && /recovery|restoration|technical|legal|lawyer|attorney|counsel|revenue|statement|payout/i.test(item.type);
    let verifiedAmount: number | undefined;
    if (verified && financial) {
      const raw = window.prompt('Enter the monetary amount verified from this evidence (₹):', String(item.verified_amount || ''));
      if (raw === null) return;
      verifiedAmount = Number(raw);
      if (!Number.isFinite(verifiedAmount) || verifiedAmount < 0) {
        setError('Enter a valid non-negative verified amount.');
        return;
      }
    }
    await run((id) => verifyEvidence(id, evidenceId, verified, reason.trim(), verifiedAmount), `Evidence ${verified ? 'verified' : 'rejected'}.`);
  }

  async function updateExclusion() {
    if (!selected) return;
    const choices = ['INTENTIONAL_SELF_INFLICTED', 'FRAUDULENT_CLAIM', 'UNSUPPORTED_LOSS', 'NON_COVERED_PLATFORM_VIOLATION', 'PRE_EXISTING_INCIDENT'];
    const selectedCode = window.prompt(`Enter an exclusion code:\n${choices.join('\n')}\nLeave blank to clear an existing flag.`, selected.exclusion_code || '');
    if (selectedCode === null) return;
    const code = selectedCode.trim().toUpperCase() || null;
    if (code && !choices.includes(code)) {
      setError('Choose one of the listed exclusion codes.');
      return;
    }
    const reason = window.prompt('Adjuster rationale for this exclusion update:');
    if (!reason?.trim()) return;
    await run((id) => recordExclusion(id, code, reason.trim()), code ? 'Exclusion flag recorded.' : 'Exclusion flag cleared.');
  }

  async function toggleAudit() {
    if (!selected) return;
    if (auditRows) {
      setAuditRows(null);
      return;
    }
    setError('');
    try {
      setAuditRows(await audit('Claim', selected.id));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Audit history could not be loaded.');
    }
  }

  const title = isAdjuster ? 'Claims workbench' : 'Your claims';
  if (loading) return <div className="loading">Loading claims…</div>;
  return <>
    <div className="page-head"><div><span className="eyebrow">{isAdjuster ? 'CLAIMCENTER SIMULATOR' : 'CLAIM CENTER'}</span><h2>{title}</h2><p>{isAdjuster ? 'Investigate, assess and adjudicate with an auditable human-in-the-loop workflow.' : 'Track every stage of your claim and provide supporting evidence.'}</p></div><button className="secondary" onClick={() => void refresh()}><RefreshCw size={15}/> Refresh</button></div>
    {error && <Card className="inline-alert"><b>Could not complete action</b><p>{error}</p></Card>}
    {notice && <div className="success">{notice}</div>}
    <div className="claim-layout">
      <Card className="claim-list"><div className="list-head"><b>Claims queue</b><span>{rows.length} total</span></div>
        {rows.length === 0 ? <div className="empty"><FileCheck2 size={32}/><h3>No claims yet</h3><p>Report an incident to create a claim.</p></div> : rows.map((claim) => <button className={`claim-item ${selectedId === claim.id ? 'selected' : ''}`} key={claim.id} onClick={() => { setSelectedId(claim.id); setAuditRows(null); }}>
          <div><b>{claim.number}</b><span>{claim.status.replace(/_/g, ' ')}</span></div><div><strong>{money(claim.recommended_payout)}</strong><Badge>{claim.risk_level}</Badge></div>
        </button>)}
      </Card>
      <Card className="claim-detail">{!selected ? <div className="empty"><FileCheck2 size={38}/><h3>Select a claim</h3><p>Choose a claim from the queue to open the investigation workbench.</p></div> : <>
        <div className="claim-title"><div><span className="eyebrow">{selected.number} · {selected.policy_number}</span><h3>{String(selected.incident_type || 'Claim').replace(/_/g, ' ')}</h3><span className="claim-meta">{selected.platform} · Incident date {selected.incident_date}</span>{selected.exclusion_code && <span className="claim-meta exclusion-flag">Exclusion review: {selected.exclusion_code}</span>}{selected.reason && <span className="claim-meta">{selected.reason}</span>}</div><Badge>{selected.status}</Badge></div>
        <div className="stats compact"><Stat label="Claimed" value={money(selected.claimed_amount)} icon={<IndianRupee/>}/><Stat label="Eligible" value={money(selected.eligible_amount)} icon={<Scale/>}/><Stat label="Recommended" value={money(selected.recommended_payout)} icon={<BrainCircuit/>}/></div>
        <div className="work-grid">
          <div><div className="section-title"><h4>Evidence</h4>{!isAdjuster && canAddEvidence && <button className="secondary small" disabled={busy} onClick={() => void requestEvidence()}><Upload size={14}/> Add reference</button>}</div>
            {selected.evidence.length ? selected.evidence.map((item: any) => <div className="evidence" key={item.id}><FileCheck2/><div><b>{item.type}</b><span>{item.file}</span>{item.verified_amount > 0 && <small>Verified amount: {money(item.verified_amount)}</small>}{item.notes && <small>{item.notes}</small>}</div><div className="evidence-actions"><Badge>{item.status}</Badge>{isAdjuster && !finalized && item.status !== 'REJECTED' && <><button className="icon-button" title={item.status === 'VERIFIED' ? 'Confirm or update amount' : 'Verify evidence'} disabled={busy} onClick={() => void verifyItem(item.id, true)}><CheckCircle2 size={15}/></button><button className="icon-button danger" title="Reject evidence" disabled={busy} onClick={() => void verifyItem(item.id, false)}><AlertTriangle size={15}/></button></>}</div></div>) : <div className="empty compact-empty">No evidence has been referenced.</div>}
            <h4 className="subhead">Exposures</h4>{selected.exposures.map((exposure: any) => <div className="exposure-row" key={exposure.id}><span>{exposure.coverage}</span><span>Claimed {money(exposure.claimed)}</span><strong>Eligible {money(exposure.eligible)}</strong></div>)}
          </div>
          <div><div className="section-title"><h4>AI investigation</h4><Badge>{selected.risk_level} RISK</Badge></div>
            {selected.assessments.length ? selected.assessments.map((assessment: any, index: number) => <div className="agent" key={`${assessment.agent}-${index}`}><div className="agent-top"><b>{assessment.agent}</b><span>{Math.round(assessment.confidence * 100)}%</span></div><p>{assessment.findings}</p><small>Recommendation: {assessment.recommendation}</small></div>) : <div className="empty compact-empty">Run the investigation to generate structured AI findings.</div>}
            <div className="loss-breakdown"><b>Loss assessment</b><div><span>Gross eligible loss</span><strong>{money(selected.eligible_amount)}</strong></div><div><span>Illustrative payout</span><strong>{money(selected.recommended_payout)}</strong></div>{selected.payment && <div><span>Payment · {selected.payment.reference}</span><strong>{money(selected.payment.amount)} · {selected.payment.status}</strong></div>}</div>
            {isAdjuster && <div className="action-row">
              {canInvestigate && <button className="secondary" disabled={busy} onClick={() => void run(investigate, 'AI investigation completed.')}><BrainCircuit size={16}/> Run AI investigation</button>}
              {canAssess && <button className="secondary" disabled={busy} onClick={() => void run(assess, 'Deterministic coverage rules and loss assessment completed.')}><Scale size={16}/> Evaluate rules & loss</button>}
              {!['APPROVED','PAYMENT_PENDING','PAID','DENIED','CLOSED'].includes(selected.status) && <button className="secondary" disabled={busy} onClick={() => void updateExclusion()}>Update exclusion</button>}
              {selected.status === 'PENDING_APPROVAL' && <button className="primary" disabled={busy} onClick={() => void manualDecision('APPROVE')}>Approve claim</button>}
              {['PENDING_APPROVAL','COVERAGE_REVIEW'].includes(selected.status) && <button className="danger-button" disabled={busy} onClick={() => void manualDecision('DENY')}>Deny claim</button>}
              {['OPEN','INITIAL_REVIEW','INVESTIGATION','COVERAGE_REVIEW','LOSS_ASSESSMENT','PENDING_APPROVAL'].includes(selected.status) && <button className="secondary" disabled={busy} onClick={() => void manualDecision('REQUEST_INFORMATION')}>Request information</button>}
              {selected.status === 'PAYMENT_PENDING' && <button className="primary" disabled={busy} onClick={() => void run(pay, 'Claim payment recorded.')}><IndianRupee size={16}/> Process payment</button>}
              {(selected.status === 'PAID' || selected.status === 'DENIED') && <button className="secondary" disabled={busy} onClick={() => void run(closeClaim, 'Claim closed.')}>Close claim</button>}
            </div>}
          </div>
        </div>
        <div className="decision-bar"><div><History size={18}/><span>AI assists · deterministic rules control coverage · authorized adjuster controls approval</span></div><button className="ghost" onClick={() => void toggleAudit()}>{auditRows ? 'Hide audit trail' : 'View audit trail'}</button></div>
        {auditRows && <div className="audit-list">{auditRows.length ? auditRows.map((event, index) => <div className="audit-event" key={`${event.timestamp}-${index}`}><b>{event.action}</b><span>{event.actor} · {event.role} · {new Date(event.timestamp).toLocaleString()}</span>{event.details && <p>{event.details}</p>}</div>) : <div className="empty compact-empty">No audit events recorded yet.</div>}</div>}
      </>}</Card>
    </div>
  </>;
}
