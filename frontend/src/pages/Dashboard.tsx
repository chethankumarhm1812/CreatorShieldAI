import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip, BarChart, Bar, XAxis, YAxis } from 'recharts';
import { ShieldCheck, AlertTriangle, IndianRupee, Activity, ArrowUpRight, Clock3, RefreshCw } from 'lucide-react';
import { claims as getClaims, dashboard } from '../services/api';
import { Card, Stat, Badge, Progress } from '../components/UI';

const colors = ['#4cc9f0', '#48d6b0', '#f0bd58', '#f5798a', '#8a9bff'];
const money = (value = 0) => `₹${Number(value).toLocaleString('en-IN')}`;
const stages = ['OPEN', 'INVESTIGATION', 'EVIDENCE_REQUIRED', 'COVERAGE_REVIEW', 'PENDING_APPROVAL', 'PAYMENT_PENDING', 'PAID', 'CLOSED'];

export default function Dashboard({ user }: { user: any }) {
  const [data, setData] = useState<any>();
  const [claimRows, setClaimRows] = useState<any[]>([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const refresh = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const [summary, rows] = await Promise.all([dashboard(), getClaims()]);
      setData(summary);
      setClaimRows(rows);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Dashboard data could not be loaded.');
    } finally {
      setLoading(false);
    }
  }, []);
  useEffect(() => { void refresh(); }, [refresh]);

  if (loading) return <div className="loading">Loading operations…</div>;
  if (error) return <Card className="error-state"><h3>Dashboard unavailable</h3><p>{error}</p><button className="secondary" onClick={() => void refresh()}><RefreshCw size={16}/> Retry</button></Card>;

  if (user.role === 'CREATOR') {
    const latest = claimRows[0];
    const currentStage = latest ? Math.max(0, stages.indexOf(latest.status)) : -1;
    return <>
      <div className="welcome"><div><span className="eyebrow">GOOD AFTERNOON, {user.name.split(' ')[0].toUpperCase()}</span><h2>Your creator business is protected.</h2><p>Monitor policy health, security posture and claim activity from one place.</p><div className="quick-actions"><Link className="primary" to="/policy">Get a quote <ArrowUpRight size={15}/></Link><Link className="secondary" to="/report">Report incident</Link><Link className="secondary" to="/billing">View billing</Link></div></div><div className="shield-orb"><ShieldCheck size={40}/></div></div>
      <div className="stats">
        <Stat label="Policy status" value={data.policy?.status || 'No policy'} sub={data.policy?.number || 'Get a quote to begin'} icon={<Badge>{data.policy?.status || 'UNINSURED'}</Badge>}/>
        <Stat label="Coverage" value={money(data.policy?.aggregate_limit)} sub="Aggregate limit" icon={<ShieldCheck size={20}/>}/>
        <Stat label="Security score" value={`${data.security_score || 0}/100`} sub="Account posture" icon={<Activity size={20}/>}/>
        <Stat label="Open claims" value={data.open_claims ?? 0} sub="Requires attention" icon={<AlertTriangle size={20}/>}/>
      </div>
      <div className="grid2">
        <Card><div className="section-title"><div><span className="eyebrow">POLICY HEALTH</span><h3>{data.policy?.product || 'No active policy'}</h3></div><Badge>{data.policy?.status || 'NOT INSURED'}</Badge></div>
          {data.policy ? <><div className="coverage-big"><strong>{money(data.policy.aggregate_limit)}</strong><span>total insured limit</span></div><Progress value={Math.min(100, data.policy.aggregate_limit ? (data.policy.deductible / data.policy.aggregate_limit) * 100 : 0)}/><div className="mini-grid">{data.policy.coverages.slice(0, 3).map((coverage: any) => <div key={coverage.code}><span>{coverage.name}</span><b>{money(coverage.limit)}</b></div>)}</div></> : <div className="empty"><p>Start with an eligibility-based quote for creator account protection.</p><Link className="primary" to="/policy">Explore coverage</Link></div>}
        </Card>
        <Card><div className="section-title"><div><span className="eyebrow">CLAIMS JOURNEY</span><h3>{latest ? latest.number : 'No reported claims'}</h3></div><Link to="/claims"><ArrowUpRight size={19}/></Link></div>
          {latest ? <><div className="timeline">{['FNOL received', 'Investigation', 'Coverage review', 'Adjuster decision', 'Payment'].map((label, index) => <div className={index < currentStage ? 'done' : index === currentStage ? 'current' : ''} key={label}><b>{label}</b><span>{index === currentStage ? latest.status.replace(/_/g, ' ') : index < currentStage ? 'Completed' : 'Upcoming'}</span></div>)}</div><Link className="secondary small" to="/claims">Open claim details</Link></> : <div className="empty"><p>When you report an incident, its live status appears here.</p><Link className="secondary" to="/report">Report an incident</Link></div>}
        </Card>
      </div>
    </>;
  }

  const claimsByType = Object.entries(claimRows.reduce((group: Record<string, number>, claim: any) => {
    const label = String(claim.incident_type || 'OTHER').replace(/_/g, ' ');
    group[label] = (group[label] || 0) + 1;
    return group;
  }, {})).map(([name, value]) => ({ name, value }));
  const riskData = Object.entries(claimRows.reduce((group: Record<string, number>, claim: any) => {
    const label = claim.risk_level || 'UNASSESSED';
    group[label] = (group[label] || 0) + 1;
    return group;
  }, {})).map(([name, value]) => ({ name, value }));
  return <>
    <div className="welcome"><div><span className="eyebrow">INSURER CONTROL TOWER · SIMULATOR</span><h2>Claims and policy operations at a glance.</h2><p>Review risk, exposure, adjudication queues and premium flow.</p></div><div className="shield-orb"><ShieldCheck size={40}/></div></div>
    <div className="stats"><Stat label="Active policies" value={data.metrics.active_policies} icon={<ShieldCheck/>}/><Stat label="Open claims" value={data.metrics.open_claims} icon={<AlertTriangle/>}/><Stat label="Pending approval" value={data.metrics.pending_approval} icon={<Clock3/>}/><Stat label="Premium collected" value={money(data.metrics.premium_collected)} icon={<IndianRupee/>}/></div>
    <div className="stats"><Stat label="Open exposure" value={money(data.metrics.total_exposure)} sub="Eligible loss under review"/><Stat label="High-risk claims" value={claimRows.filter((claim) => claim.risk_level === 'HIGH').length} sub="Human review required"/><Stat label="Total claims" value={claimRows.length} sub="Across all claim statuses"/></div>
    <div className="grid2 charts-grid">
      <Card><div className="section-title"><div><span className="eyebrow">CLAIM MIX</span><h3>Claims by incident</h3></div></div>{claimsByType.length ? <div className="chart-wrap"><ResponsiveContainer width="100%" height={230}><PieChart><Pie data={claimsByType} dataKey="value" nameKey="name" outerRadius={82} label>{claimsByType.map((entry, index) => <Cell key={entry.name} fill={colors[index % colors.length]}/>)}</Pie><Tooltip/></PieChart></ResponsiveContainer></div> : <div className="empty">No claims have been reported.</div>}</Card>
      <Card><div className="section-title"><div><span className="eyebrow">RISK DISTRIBUTION</span><h3>Investigation referrals</h3></div></div>{riskData.length ? <div className="chart-wrap"><ResponsiveContainer width="100%" height={230}><BarChart data={riskData}><XAxis dataKey="name" stroke="#748ba3"/><YAxis allowDecimals={false} stroke="#748ba3"/><Tooltip/><Bar dataKey="value" fill="#4cc9f0" radius={[6, 6, 0, 0]}/></BarChart></ResponsiveContainer></div> : <div className="empty">Risk indicators appear after investigation.</div>}</Card>
    </div>
    <div className="grid2">
      <Card><div className="section-title"><div><span className="eyebrow">OPERATING MODEL</span><h3>Guidewire-inspired core</h3></div></div><div className="architecture-mini"><div><b>PolicyCenter Simulator</b><span>Product · Quote · Underwriting · Policy</span></div><div><b>ClaimCenter Simulator</b><span>FNOL · Investigation · Adjudication</span></div><div><b>BillingCenter Simulator</b><span>Invoice · Payment · Collections</span></div></div></Card>
      <Card><div className="section-title"><div><span className="eyebrow">CONTROL PRINCIPLE</span><h3>AI assists. Rules decide. Humans approve.</h3></div></div><p className="large-copy">The platform uses AI for triage, evidence analysis and loss recommendations, while deterministic insurance rules and authorized adjusters control consequential decisions.</p><Link className="secondary" to="/claims">Open claims workbench</Link></Card>
    </div>
  </>;
}
