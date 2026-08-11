import { useMemo } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useTemplates, useCategories } from '../api/queries';
import { useAuthStore } from '../store/authStore';
import { Plus, Folder, Search, FileText } from 'lucide-react';
import TemplateCard from '../components/TemplateCard';
import EmptyState from '../components/EmptyState';
import DataError from '../components/DataError';

const TemplatePage = () => {
  const navigate = useNavigate();
  const { data: templates, isLoading, isError } = useTemplates();
  const { data: categories } = useCategories();
  const [searchParams, setSearchParams] = useSearchParams();
  const currentUser = useAuthStore((s) => s.user);
  const canAuthor = currentUser?.role === 'Admin' || currentUser?.role === 'Editor';

  const selectedCategory = searchParams.get('category');
  const query = searchParams.get('q') || '';
  const effectiveMode = canAuthor && searchParams.get('view') === 'manage' ? 'manage' : 'use';

  const setSelectedCategory = (cat: string | null) => {
    const next = new URLSearchParams(searchParams);
    if (cat) next.set('category', cat); else next.delete('category');
    setSearchParams(next);
  };

  const setViewMode = (mode: 'use' | 'manage') => {
    const next = new URLSearchParams(searchParams);
    if (mode === 'manage') next.set('view', 'manage'); else next.delete('view');
    setSearchParams(next);
  };

  const setQuery = (q: string) => {
    const next = new URLSearchParams(searchParams);
    if (q) next.set('q', q); else next.delete('q');
    setSearchParams(next, { replace: true });
  };

  const filteredTemplates = useMemo(() => {
    let list = templates || [];
    if (selectedCategory) list = list.filter(t => t.category === selectedCategory);
    if (query.trim()) {
      const q = query.toLowerCase();
      list = list.filter(t =>
        t.name.toLowerCase().includes(q) ||
        t.category.toLowerCase().includes(q) ||
        t.owner.toLowerCase().includes(q) ||
        t.tags?.some(tag => tag.toLowerCase().includes(q))
      );
    }
    return list;
  }, [templates, selectedCategory, query]);

  if (isLoading) return <div>Loading templates...</div>;
  if (isError) return <DataError message="Couldn't load the template library. Check that the server is running and try again." />;

  return (
    <div className="template-browser" style={{ display: 'flex', height: '100%', gap: '24px' }}>
      {/* Folder sidebar */}
      <div className="template-browser-sidebar" style={{ width: '220px', flexShrink: 0 }}>
        <h2 style={{ marginBottom: '16px' }}>Categories</h2>

        <ul style={{ listStyle: 'none' }}>
          <li
            className={`nav-item ${selectedCategory === null ? 'active' : ''}`}
            style={{ marginBottom: '2px' }}
            onClick={() => setSelectedCategory(null)}
          >
            <Folder />
            <span>All Templates</span>
          </li>
          {categories?.map(cat => (
            <li
              key={cat}
              className={`nav-item ${selectedCategory === cat ? 'active' : ''}`}
              style={{ marginBottom: '2px' }}
              onClick={() => setSelectedCategory(cat)}
            >
              <Folder />
              <span>{cat}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* Main Library */}
      <div style={{ flex: 1, minWidth: 0 }}>
        <div className="page-header">
          <div>
            <h1>{selectedCategory || 'All Templates'}</h1>
            <p className="page-subtitle">{filteredTemplates.length} template{filteredTemplates.length === 1 ? '' : 's'}</p>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            {canAuthor && (
              <div style={{ display: 'flex', backgroundColor: 'var(--bg-hover)', borderRadius: 'var(--radius-sm)', padding: '3px' }}>
                <button
                  className={`btn ${effectiveMode === 'use' ? '' : 'btn-outline'}`}
                  style={{ padding: '6px 14px', fontSize: '0.82rem', backgroundColor: effectiveMode === 'use' ? undefined : 'transparent', border: 'none' }}
                  onClick={() => setViewMode('use')}
                >
                  Use Templates
                </button>
                <button
                  className={`btn ${effectiveMode === 'manage' ? '' : 'btn-outline'}`}
                  style={{ padding: '6px 14px', fontSize: '0.82rem', backgroundColor: effectiveMode === 'manage' ? undefined : 'transparent', border: 'none' }}
                  onClick={() => setViewMode('manage')}
                >
                  Manage
                </button>
              </div>
            )}
            {effectiveMode === 'manage' && (
              <button className="btn" onClick={() => navigate('/templates/new')}>
                <Plus size={18} /> New Template
              </button>
            )}
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', backgroundColor: 'var(--bg-surface)', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-sm)', padding: '10px 14px', marginBottom: '24px', maxWidth: '360px' }}>
          <Search size={16} color="var(--text-tertiary)" />
          <input
            type="text"
            placeholder="Search this category..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            style={{ background: 'transparent', border: 'none', outline: 'none', width: '100%', fontSize: '0.9rem', color: 'var(--text-primary)' }}
          />
        </div>

        {filteredTemplates.length === 0 ? (
          <EmptyState
            icon={FileText}
            title="No templates found"
            description="Try a different category or search term."
            actionLabel={effectiveMode === 'manage' ? "New Template" : undefined}
            onAction={effectiveMode === 'manage' ? () => navigate('/templates/new') : undefined}
          />
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '20px' }}>
            {filteredTemplates.map(t => <TemplateCard key={t.id} template={t} mode={effectiveMode} />)}
          </div>
        )}
      </div>
    </div>
  );
};

export default TemplatePage;
