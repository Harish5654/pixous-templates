import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTemplates } from '../api/queries';
import { useFavoritesStore } from '../store/favoritesStore';
import { useRecentStore } from '../store/recentStore';
import { useAuthStore } from '../store/authStore';
import { FileText, CheckCircle2, FileEdit, Star, Plus } from 'lucide-react';
import StatCard from '../components/StatCard';
import EmptyState from '../components/EmptyState';
import DataError from '../components/DataError';
import FillAndGenerateModal from '../components/FillAndGenerateModal';
import type { Template } from '../types/template';

const Dashboard = () => {
  const navigate = useNavigate();
  const { data: templates, isLoading, isError } = useTemplates();
  const { favoriteIds } = useFavoritesStore();
  const { recentIds } = useRecentStore();
  const currentUser = useAuthStore((s) => s.user);
  const canAuthor = currentUser?.role === 'Admin' || currentUser?.role === 'Editor';
  const [previewTemplate, setPreviewTemplate] = useState<Template | null>(null);

  if (isLoading) return <div>Loading dashboard...</div>;
  if (isError) return <DataError message="Couldn't load the dashboard. Check that the server is running and try again." />;

  const totalTemplates = templates?.length || 0;
  const publishedTemplates = templates?.filter(t => t.status === 'Published').length || 0;
  const draftTemplates = templates?.filter(t => t.status === 'Draft').length || 0;

  const openTemplate = (t: Template) => {
    if (canAuthor) navigate(`/templates/${t.id}/edit`);
    else setPreviewTemplate(t);
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Dashboard</h1>
          <p className="page-subtitle">Welcome back, {currentUser?.name?.split(' ')[0] || 'there'}.</p>
        </div>
        {canAuthor && (
          <button className="btn" onClick={() => navigate('/templates/new')}>
            <Plus size={16} /> New Template
          </button>
        )}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginBottom: '32px' }}>
        <StatCard label="Total Templates" value={totalTemplates} icon={FileText} />
        <StatCard label="Published" value={publishedTemplates} icon={CheckCircle2} accent="success" />
        <StatCard label="Drafts" value={draftTemplates} icon={FileEdit} accent="warning" />
        <StatCard label="Favorites" value={favoriteIds.length} icon={Star} />
        <StatCard label="Recently Opened" value={recentIds.length} icon={FileEdit} />
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
        <h2 style={{ marginBottom: 0 }}>Recently Updated</h2>
        <span style={{ fontSize: '0.85rem', color: 'var(--accent-primary)', cursor: 'pointer', fontWeight: 500 }} onClick={() => navigate('/templates')}>
          View all
        </span>
      </div>
      <div className="card" style={{ padding: '0', marginTop: '16px' }}>
        {totalTemplates === 0 ? (
          <EmptyState
            icon={FileText}
            title="No templates yet"
            description={canAuthor ? "Create your first template to get started." : "Check back once your team has published some templates."}
            actionLabel={canAuthor ? "New Template" : undefined}
            onAction={canAuthor ? () => navigate('/templates/new') : undefined}
          />
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-color)', textAlign: 'left' }}>
                <th style={{ padding: '14px 20px', fontSize: '0.78rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>Name</th>
                <th style={{ padding: '14px 20px', fontSize: '0.78rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>Category</th>
                <th style={{ padding: '14px 20px', fontSize: '0.78rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>Status</th>
                <th style={{ padding: '14px 20px', fontSize: '0.78rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>Updated By</th>
              </tr>
            </thead>
            <tbody>
              {templates?.slice(0, 5).map(t => (
                <tr key={t.id} style={{ borderBottom: '1px solid var(--border-color)', cursor: 'pointer' }} onClick={() => openTemplate(t)}>
                  <td style={{ padding: '16px 20px', fontWeight: 500 }}>{t.name}</td>
                  <td style={{ padding: '16px 20px', color: 'var(--text-secondary)' }}>{t.category}</td>
                  <td style={{ padding: '16px 20px' }}>
                    <span className={`badge ${t.status === 'Published' ? 'badge-success' : 'badge-warning'}`}>
                      {t.status}
                    </span>
                  </td>
                  <td style={{ padding: '16px 20px', color: 'var(--text-secondary)' }}>{t.updated_by}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {previewTemplate && <FillAndGenerateModal template={previewTemplate} onClose={() => setPreviewTemplate(null)} />}
    </div>
  );
};

export default Dashboard;
