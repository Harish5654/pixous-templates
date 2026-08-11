import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useLogin } from '../api/queries';
import { useAuthStore } from '../store/authStore';

// Per-role demo credentials. Picking a role auto-fills the email and password
// so nobody has to remember or display the shared password.
const ROLE_ACCOUNTS = [
  { role: 'Admin', email: 'admin@pixoustech.com', password: 'Admin@123' },
  { role: 'Editor', email: 'editor@pixoustech.com', password: 'Editor@123' },
  { role: 'Employee', email: 'employee@pixoustech.com', password: 'Employee@123' },
];

const LoginPage = () => {
  const navigate = useNavigate();
  const location = useLocation() as { state?: { from?: string } };
  const login = useLogin();
  const setAuth = useAuthStore((s) => s.login);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleRoleSelect = (role: string) => {
    const acc = ROLE_ACCOUNTS.find(a => a.role === role);
    if (acc) {
      setEmail(acc.email);
      setPassword(acc.password);
      setError('');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    try {
      const data = await login.mutateAsync({ email, password });
      setAuth(data.access_token, data.user);
      navigate(location.state?.from || '/dashboard', { replace: true });
    } catch {
      setError('Invalid email or password.');
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: 'var(--bg-canvas)' }}>
      <div className="card" style={{ width: '380px' }}>
        <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '24px' }}>
          <img src="/pixous_logo.png" alt="Pixous Technologies" style={{ height: '70px' }} />
        </div>
        <h2 style={{ textAlign: 'center', marginBottom: '4px' }}>Sign in</h2>
        <p style={{ textAlign: 'center', color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '24px' }}>
          Pixous Template Engine
        </p>

        <div className="form-group">
          <label className="form-label">Sign in as</label>
          <select
            className="form-input"
            defaultValue=""
            onChange={(e) => handleRoleSelect(e.target.value)}
          >
            <option value="" disabled>Select a role...</option>
            {ROLE_ACCOUNTS.map(a => (
              <option key={a.role} value={a.role}>{a.role}</option>
            ))}
          </select>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)', marginTop: '6px', marginBottom: 0 }}>
            Picking a role fills in the demo credentials for you — or type your own below.
          </p>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">Email</label>
            <input type="email" className="form-input" value={email} onChange={(e) => setEmail(e.target.value)} required autoFocus />
          </div>
          <div className="form-group">
            <label className="form-label">Password</label>
            <input type="password" className="form-input" value={password} onChange={(e) => setPassword(e.target.value)} required />
          </div>

          {error && <p style={{ color: 'var(--danger)', fontSize: '0.85rem', marginBottom: '12px' }}>{error}</p>}

          <button type="submit" className="btn" style={{ width: '100%', justifyContent: 'center' }} disabled={login.isPending}>
            {login.isPending ? 'Signing in...' : 'Sign in'}
          </button>
        </form>

        <p style={{ textAlign: 'center', fontSize: '0.78rem', color: 'var(--text-tertiary)', marginTop: '16px', marginBottom: 0 }}>
          Forgot your password? Ask an administrator to reset it from <strong>Settings → Users &amp; Password Reset</strong>.
        </p>
      </div>
    </div>
  );
};

export default LoginPage;
