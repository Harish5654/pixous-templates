import { useState } from 'react';
import { User, Palette, PanelLeft, KeyRound, Copy, Check, ShieldAlert } from 'lucide-react';
import { useUIStore } from '../store/uiStore';
import { useAuthStore } from '../store/authStore';
import { useResetPassword, useUsers } from '../api/queries';
import DataError from '../components/DataError';
import type { User as UserAccount } from '../types/user';
import Accordion from '../components/Accordion';

const SettingsPage = () => {
  const { sidebarOpen, toggleSidebar } = useUIStore();
  const currentUser = useAuthStore((s) => s.user);
  const isAdmin = currentUser?.role === 'Admin';

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Settings</h1>
          <p className="page-subtitle">Manage your profile and workspace preferences.</p>
        </div>
      </div>

      <div style={{ maxWidth: '640px' }}>
        <Accordion title="Profile" icon={<User size={16} />} defaultOpen>
          <div className="form-group">
            <label className="form-label">Name</label>
            <input className="form-input" value={currentUser?.name || ''} readOnly />
          </div>
          <div className="form-group">
            <label className="form-label">Email</label>
            <input className="form-input" value={currentUser?.email || ''} readOnly />
          </div>
          <div className="form-group">
            <label className="form-label">Role</label>
            <input className="form-input" value={currentUser?.role || ''} readOnly />
          </div>
        </Accordion>

        {isAdmin && <UserManagement />}

        <Accordion title="Appearance" icon={<Palette size={16} />}>
          <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
            This workspace currently uses a single light enterprise theme. Additional theme options may be added in a future release.
          </p>
        </Accordion>

        <Accordion title="Sidebar" icon={<PanelLeft size={16} />}>
          <label style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '0.9rem', cursor: 'pointer' }}>
            <input type="checkbox" checked={sidebarOpen} onChange={toggleSidebar} />
            Keep sidebar expanded
          </label>
        </Accordion>
      </div>
    </div>
  );
};

const UserManagement = () => {
  const { data: users, isLoading, isError } = useUsers();
  const resetPassword = useResetPassword();
  const [resetTarget, setResetTarget] = useState<UserAccount | null>(null);
  const [customPassword, setCustomPassword] = useState('');
  const [result, setResult] = useState<{ email: string; password: string } | null>(null);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState('');

  const openReset = (user: UserAccount) => {
    setResetTarget(user);
    setCustomPassword('');
    setResult(null);
    setError('');
    setCopied(false);
  };

  const handleReset = async () => {
    if (!resetTarget) return;
    setError('');
    setCopied(false);
    try {
      const data = await resetPassword.mutateAsync({
        userId: resetTarget.id,
        password: customPassword.trim() || undefined,
      });
      setResult({ email: data.email, password: data.password });
      setResetTarget(null);
      setCustomPassword('');
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Password reset failed. Please try again.');
    }
  };

  const copyPassword = async () => {
    if (!result) return;
    try {
      await navigator.clipboard.writeText(result.password);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setCopied(false);
    }
  };

  return (
    <Accordion title="Users & Password Reset" icon={<KeyRound size={16} />}>
      <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: 0 }}>
        Forgot password? Users who can't sign in can get a new password here — it's shown to you once so you can share it with them.
      </p>

      {isLoading ? (
        <p style={{ fontSize: '0.85rem', color: 'var(--text-tertiary)' }}>Loading users…</p>
      ) : isError ? (
        <DataError message="Couldn't load users. Check that the server is running and try again." />
      ) : (
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--border-color)', textAlign: 'left' }}>
              <th style={{ padding: '10px 12px', fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>Name</th>
              <th style={{ padding: '10px 12px', fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>Email</th>
              <th style={{ padding: '10px 12px', fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>Role</th>
              <th style={{ padding: '10px 12px', fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.04em' }}></th>
            </tr>
          </thead>
          <tbody>
            {(users || []).map((u) => (
              <tr key={u.id} style={{ borderBottom: '1px solid var(--border-color)' }}>
                <td style={{ padding: '12px', fontWeight: 500 }}>{u.name}</td>
                <td style={{ padding: '12px', color: 'var(--text-secondary)' }}>{u.email}</td>
                <td style={{ padding: '12px' }}>
                  <span className="badge badge-neutral">{u.role}</span>
                </td>
                <td style={{ padding: '12px', textAlign: 'right' }}>
                  <button className="btn btn-outline" style={{ padding: '6px 12px', fontSize: '0.8rem' }} onClick={() => openReset(u)}>
                    Reset password
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {resetTarget && (
        <div style={{ marginTop: '16px', padding: '14px', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-md)', backgroundColor: 'var(--bg-elevated, #fafbfc)' }}>
          <div style={{ fontSize: '0.9rem', fontWeight: 600, marginBottom: '4px' }}>
            Reset password for {resetTarget.name}
          </div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '12px' }}>{resetTarget.email}</div>
          <div className="form-group">
            <label className="form-label">New password (optional)</label>
            <input
              className="form-input"
              type="text"
              value={customPassword}
              onChange={(e) => setCustomPassword(e.target.value)}
              placeholder="Leave blank to auto-generate a secure password"
            />
          </div>
          {error && <p style={{ color: 'var(--danger)', fontSize: '0.85rem', margin: '0 0 10px' }}>{error}</p>}
          <div style={{ display: 'flex', gap: '10px' }}>
            <button className="btn" onClick={handleReset} disabled={resetPassword.isPending}>
              {resetPassword.isPending ? 'Resetting…' : 'Reset password'}
            </button>
            <button className="btn btn-outline" onClick={() => setResetTarget(null)}>
              Cancel
            </button>
          </div>
        </div>
      )}

      {result && (
        <div style={{ marginTop: '16px', padding: '14px', border: '1px solid var(--success, #2e7d32)', borderRadius: 'var(--radius-md)', backgroundColor: 'var(--success-soft, #f0faf0)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.9rem', fontWeight: 600, marginBottom: '8px' }}>
            <ShieldAlert size={16} /> New password for {result.email}
          </div>
          <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
            <code style={{ padding: '8px 12px', backgroundColor: '#fff', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-sm, 6px)', fontSize: '0.95rem', wordBreak: 'break-all' }}>
              {result.password}
            </code>
            <button className="btn btn-outline" style={{ padding: '6px 12px', fontSize: '0.8rem', flexShrink: 0 }} onClick={copyPassword}>
              {copied ? <Check size={14} /> : <Copy size={14} />}
              {copied ? 'Copied' : 'Copy'}
            </button>
          </div>
          <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', margin: '10px 0 0' }}>
            Share this password with the user — it's shown only once. They can change it later if you add a profile password feature.
          </p>
        </div>
      )}
    </Accordion>
  );
};

export default SettingsPage;
