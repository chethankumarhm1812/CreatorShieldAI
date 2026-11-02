import React from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter, Navigate, Outlet, Route, Routes, useLocation } from 'react-router-dom';
import Layout from './components/Layout';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Policy from './pages/Policy';
import Billing from './pages/Billing';
import Report from './pages/Report';
import Claims from './pages/Claims';
import Rules from './pages/Rules';
import './styles.css';
import './responsive.css';

type User = { id: number; name: string; email: string; role: 'CREATOR' | 'ADJUSTER' };

function getUser(): User | null {
  try {
    const user = JSON.parse(localStorage.getItem('user') || 'null');
    if (user && Number.isInteger(user.id) && typeof user.name === 'string' &&
        ['CREATOR', 'ADJUSTER'].includes(user.role) && localStorage.getItem('token')) {
      return user as User;
    }
  } catch {
    // Invalid local session data is cleared below.
  }
  localStorage.removeItem('user');
  localStorage.removeItem('token');
  return null;
}

function ProtectedLayout() {
  const user = getUser();
  if (!user) return <Navigate to="/login" replace />;
  return <Layout user={user}><Outlet context={user} /></Layout>;
}

function App() {
  useLocation();
  const user = getUser();
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route element={<ProtectedLayout />}>
        <Route index element={<Dashboard user={user} />} />
        <Route path="/policy" element={<Policy />} />
        <Route path="/billing" element={<Billing />} />
        <Route path="/report" element={<Report />} />
        <Route path="/claims" element={<Claims user={user} />} />
        <Route path="/rules" element={<Rules />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}

createRoot(document.getElementById('root')!).render(
  <React.StrictMode><BrowserRouter><App /></BrowserRouter></React.StrictMode>,
);
