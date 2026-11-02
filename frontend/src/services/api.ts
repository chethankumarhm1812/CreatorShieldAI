const API = (import.meta.env.VITE_API_URL || 'http://localhost:8000/api').replace(/\/$/, '');

export class ApiError extends Error {
  constructor(message: string, readonly status: number) {
    super(message);
    this.name = 'ApiError';
  }
}

export async function api<T = any>(path: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem('token');
  const headers = new Headers(options.headers);
  if (!headers.has('Content-Type') && options.body) headers.set('Content-Type', 'application/json');
  if (token) headers.set('Authorization', `Bearer ${token}`);

  let response: Response;
  try {
    response = await fetch(`${API}${path}`, { ...options, headers });
  } catch {
    throw new ApiError('Unable to reach CreatorShield. Check that the API is running and try again.', 0);
  }

  if (!response.ok) {
    if (response.status === 401 && path !== '/auth/login' && path !== '/auth/register') {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.assign('/login');
    }
    const body = await response.text();
    let message = body || `Request failed (${response.status})`;
    try {
      const parsed = JSON.parse(body);
      message = typeof parsed.detail === 'string' ? parsed.detail : message;
    } catch {
      // Keep plain-text API errors readable.
    }
    throw new ApiError(message, response.status);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export const login = (email: string, password: string) =>
  api('/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) });
export const register = (details: object) =>
  api('/auth/register', { method: 'POST', body: JSON.stringify(details) });
export const creatorAccounts = () => api('/accounts');
export const addCreatorAccount = (details: object) =>
  api('/accounts', { method: 'POST', body: JSON.stringify(details) });
export const dashboard = () => api('/dashboard');
export const policies = () => api('/policies');
export const billing = () => api('/billing');
export const claims = () => api('/claims');
export const claim = (id: number) => api(`/claims/${id}`);
export const createIncident = (incident: object) =>
  api('/incidents', { method: 'POST', body: JSON.stringify(incident) });
export const createClaim = (id: number, exposures: object) =>
  api(`/claims/from-incident/${id}`, { method: 'POST', body: JSON.stringify(exposures) });
export const submitFNOL = (details: object) =>
  api('/claims/fnol', { method: 'POST', body: JSON.stringify(details) });
export const addEvidence = (id: number, evidence: object) =>
  api(`/claims/${id}/evidence`, { method: 'POST', body: JSON.stringify(evidence) });
export const verifyEvidence = (claimId: number, evidenceId: number, verified: boolean, reason: string, verifiedAmount?: number) =>
  api(`/claims/${claimId}/evidence/${evidenceId}/verify`, {
    method: 'POST',
    body: JSON.stringify({ verified, reason, verified_amount: verifiedAmount }),
  });
export const recordExclusion = (claimId: number, code: string | null, reason: string) =>
  api(`/claims/${claimId}/exclusion`, { method: 'POST', body: JSON.stringify({ code, reason }) });
export const investigate = (id: number) => api(`/claims/${id}/investigate`, { method: 'POST' });
export const assess = (id: number) => api(`/claims/${id}/assess`, { method: 'POST' });
export const decide = (id: number, decision: string, reason: string) =>
  api(`/claims/${id}/decision`, { method: 'POST', body: JSON.stringify({ decision, reason }) });
export const pay = (id: number) => api(`/claims/${id}/pay`, { method: 'POST' });
export const closeClaim = (id: number) => api(`/claims/${id}/close`, { method: 'POST' });
export const audit = (type: string, id: number) => api(`/audit/${type}/${id}`);
export const quote = (details: object) =>
  api('/quotes', { method: 'POST', body: JSON.stringify(details) });
export const bindPolicy = (details: object) =>
  api('/policies/bind', { method: 'POST', body: JSON.stringify(details) });
export const payInvoice = (invoiceId: number) =>
  api(`/billing/invoices/${invoiceId}/pay`, { method: 'POST' });
