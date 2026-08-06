import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useLogin } from '../api/queries';
import { useAuthStore } from '../store/authStore';

const LoginPage = () => {
  const navigate = useNavigate();
  const location = useLocation() as { state?: { from?: string } };
  const login = useLogin();
  const setAuth = useAuthStore((s) => s.login);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

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

        <div style={{ marginTop: '20px', padding: '12px 14px', backgroundColor: 'var(--bg-hover)', borderRadius: 'var(--radius-sm)', fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
          <strong>Demo accounts</strong> (password: <code>password123</code>):<br />
          admin@pixoustech.com · editor@pixoustech.com · employee@pixoustech.com
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
