import { useNavigate } from 'react-router-dom';
import { ClipboardCheck, Check, X, ExternalLink } from 'lucide-react';
import { useApprovals, useApproveTemplate, useRejectTemplate } from '../api/queries';
import EmptyState from '../components/EmptyState';
import DataError from '../components/DataError';
import { useAuthStore } from '../store/authStore';

const ApprovalsPage = () => {
  const navigate = useNavigate();
  const currentUser = useAuthStore((s) => s.user);
  const isAdmin = currentUser?.role === 'Admin';
  const { data: pending, isLoading, isError } = useApprovals();
  const approve = useApproveTemplate();
  const reject = useRejectTemplate();

  if (isLoading) return <div>Loading approvals...</div>;
  if (isError) return <DataError message="Couldn't load approvals. Check that the server is running and try again." />;

  const handleApprove = async (id: string, name: string) => {
    if (!window.confirm(`Approve "${name}"? It will be published immediately.`)) return;
    try {
      await approve.mutateAsync(id);
    } catch (err: any) {
      alert(`Approve failed: ${err?.response?.data?.detail || err.message}`);
    }
  };

  const handleReject = async (id: string, name: string) => {
    if (!window.confirm(`Reject "${name}"? It will be sent back to Draft.`)) return;
    try {
      await reject.mutateAsync(id);
    } catch (err: any) {
      alert(`Reject failed: ${err?.response?.data?.detail || err.message}`);
    }
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Approvals</h1>
          <p className="page-subtitle">
            {isAdmin
              ? 'Review templates submitted for approval and decide whether they go live.'
              : 'Templates you submitted that are waiting for a reviewer to sign off.'}
          </p>
        </div>
      </div>

      {!pending || pending.length === 0 ? (
        <EmptyState
          icon={ClipboardCheck}
          title="Nothing awaiting approval"
          description={
            isAdmin
              ? 'When an editor submits a template for approval, it will appear here for you to review.'
              : 'Templates you submit for approval will show up here until a reviewer signs off.'
          }
        />
      ) : (
        <div className="card" style={{ padding: '0' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-color)', textAlign: 'left' }}>
                <th style={{ padding: '14px 20px', fontSize: '0.78rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>Name</th>
                <th style={{ padding: '14px 20px', fontSize: '0.78rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>Category</th>
                <th style={{ padding: '14px 20px', fontSize: '0.78rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>Submitted By</th>
                <th style={{ padding: '14px 20px', fontSize: '0.78rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>Last Updated</th>
                <th style={{ padding: '14px 20px', fontSize: '0.78rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {pending.map((t) => (
                <tr key={t.id} style={{ borderBottom: '1px solid var(--border-color)' }}>
                  <td style={{ padding: '16px 20px', fontWeight: 500 }}>{t.name}</td>
                  <td style={{ padding: '16px 20px', color: 'var(--text-secondary)' }}>{t.category}</td>
                  <td style={{ padding: '16px 20px', color: 'var(--text-secondary)' }}>{t.created_by || t.owner || '—'}</td>
                  <td style={{ padding: '16px 20px', color: 'var(--text-secondary)' }}>
                    {t.updated_at ? new Date(t.updated_at).toLocaleString() : '—'}
                  </td>
                  <td style={{ padding: '16px 20px' }}>
                    <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                      <button
                        className="btn btn-outline"
                        style={{ padding: '6px 12px', fontSize: '0.82rem' }}
                        onClick={() => navigate(`/templates/${t.id}/edit`)}
                      >
                        <ExternalLink size={14} /> Review
                      </button>
                      {isAdmin && (
                        <>
                          <button
                            className="btn"
                            style={{ padding: '6px 12px', fontSize: '0.82rem' }}
                            disabled={approve.isPending || reject.isPending}
                            onClick={() => handleApprove(t.id, t.name)}
                          >
                            <Check size={14} /> Approve
                          </button>
                          <button
                            className="btn btn-outline"
                            style={{ padding: '6px 12px', fontSize: '0.82rem', color: 'var(--danger)', borderColor: 'var(--danger)' }}
                            disabled={approve.isPending || reject.isPending}
                            onClick={() => handleReject(t.id, t.name)}
                          >
                            <X size={14} /> Reject
                          </button>
                        </>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default ApprovalsPage;
