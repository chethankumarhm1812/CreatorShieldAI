import { FormEvent, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ShieldCheck, LockKeyhole, ArrowRight } from 'lucide-react';
import { login, register } from '../services/api';

export default function Login() {
  const [creating, setCreating] = useState(false);
  const [email, setEmail] = useState('creator@example.com');
  const [password, setPassword] = useState('Creator@123');
  const [name, setName] = useState('');
  const [business, setBusiness] = useState('');
  const [platform, setPlatform] = useState('YouTube');
  const [handle, setHandle] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const navigate = useNavigate();

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError('');
    setBusy(true);
    try {
      const result = creating
        ? await register({
          email, password, full_name: name, business_name: business,
          creator_type: 'Digital Creator', platform, handle,
        })
        : await login(email, password);
      localStorage.setItem('token', result.token);
      localStorage.setItem('user', JSON.stringify(result.user));
      navigate('/');
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Authentication failed. Please try again.');
    } finally {
      setBusy(false);
    }
  }

  return <div className="login"><div className="login-left"><div className="hero-badge"><ShieldCheck size={18}/> CREATOR CYBER INSURANCE</div><h1>Protect the business<br/><em>behind the audience.</em></h1><p>CreatorShield combines policy administration, billing, claims, deterministic rules and AI-assisted investigation in one insurance operating experience.</p><div className="hero-pills"><span>Policy lifecycle</span><span>Claims intelligence</span><span>Human-in-the-loop</span></div></div>
    <div className="login-card"><div className="login-brand"><ShieldCheck/><div><b>CreatorShield AI</b><span>Guidewire-inspired insurance core</span></div></div><h2>{creating ? 'Create creator account' : 'Welcome back'}</h2><p>{creating ? 'Register a creator profile and link your first digital account.' : 'Sign in to your demo environment.'}</p>
      <form onSubmit={submit}>
        {creating && <><label>Your name<input value={name} onChange={(event) => setName(event.target.value)} autoComplete="name" minLength={2} required/></label><label>Creator business name<input value={business} onChange={(event) => setBusiness(event.target.value)} minLength={2} required/></label><label>Primary platform<select value={platform} onChange={(event) => setPlatform(event.target.value)}><option>YouTube</option><option>Instagram</option><option>TikTok</option><option>Twitch</option><option>Other</option></select></label><label>Platform handle<input value={handle} onChange={(event) => setHandle(event.target.value)} placeholder="@yourchannel" minLength={2} required/></label></>}
        <label>Email<input type="email" value={email} onChange={(event) => setEmail(event.target.value)} autoComplete="email" required/></label>
        <label>Password<input type="password" value={password} onChange={(event) => setPassword(event.target.value)} minLength={creating ? 8 : 1} autoComplete={creating ? 'new-password' : 'current-password'} required/></label>
        {error && <div className="error">{error}</div>}
        <button className="primary" disabled={busy}>{busy ? 'Please wait…' : creating ? 'Create account' : 'Sign in'} <ArrowRight size={17}/></button>
      </form>
      <button className="auth-toggle" onClick={() => { setCreating(!creating); setError(''); }}>{creating ? 'Already registered? Sign in' : 'New creator? Create an account'}</button>
      {!creating && <div className="demo-login"><b>Demo access</b><span>Creator: creator@example.com / Creator@123</span><span>Adjuster: adjuster@example.com / Adjuster@123</span></div>}
      <div className="secure"><LockKeyhole size={15}/> Demo data only · no real credentials required</div>
    </div>
  </div>;
}
