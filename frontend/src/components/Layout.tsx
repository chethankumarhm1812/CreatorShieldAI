import { ReactNode } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { ShieldCheck, LayoutDashboard, FileText, Receipt, AlertTriangle, LogOut, BrainCircuit, Settings2 } from 'lucide-react';

type User = { name: string; role: 'CREATOR' | 'ADJUSTER' };
type NavigationItem = { path: string; label: string; Icon: typeof LayoutDashboard };

export default function Layout({ children, user }: { children: ReactNode; user: User }) {
  const navigate = useNavigate();
  const items: NavigationItem[] = user.role === 'CREATOR'
    ? [
      { path: '/', label: 'Dashboard', Icon: LayoutDashboard },
      { path: '/policy', label: 'My Policy', Icon: FileText },
      { path: '/billing', label: 'Billing', Icon: Receipt },
      { path: '/report', label: 'Report Incident', Icon: AlertTriangle },
      { path: '/claims', label: 'My Claims', Icon: ShieldCheck },
    ]
    : [
      { path: '/', label: 'Operations', Icon: LayoutDashboard },
      { path: '/claims', label: 'Claims Workbench', Icon: ShieldCheck },
      { path: '/policy', label: 'PolicyCenter Simulator', Icon: FileText },
      { path: '/billing', label: 'BillingCenter Simulator', Icon: Receipt },
      { path: '/rules', label: 'Policy Rules', Icon: Settings2 },
    ];
  return <div className="app">
    <aside>
      <div className="brand"><div className="logo"><ShieldCheck/></div><div><b>CreatorShield</b><span>AI Insurance Core</span></div></div>
      <nav>{items.map(({ path, label, Icon }) => <NavLink key={path} to={path} end={path === '/'}><Icon size={18}/>{label}</NavLink>)}</nav>
      <div className="side-note"><BrainCircuit size={18}/><div><b>AI-assisted</b><span>Human-controlled decisions</span></div></div>
      <button className="logout" onClick={() => { localStorage.removeItem('token'); localStorage.removeItem('user'); navigate('/login'); }}><LogOut size={17}/>Sign out</button>
    </aside>
    <main><header><div><span className="eyebrow">{user.role === 'CREATOR' ? 'CREATOR PORTAL' : 'INSURER OPERATIONS'}</span><h1>{user.role === 'CREATOR' ? 'Protect your digital business' : 'Insurance Operations Center'}</h1></div><div className="user-chip"><div className="avatar">{user.name[0]?.toUpperCase() || '?'}</div><div><b>{user.name}</b><span>{user.role}</span></div></div></header><section className="content">{children}</section></main>
  </div>;
}
