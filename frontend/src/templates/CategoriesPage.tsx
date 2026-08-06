import { useNavigate } from 'react-router-dom';
import { useCategories, useTemplates } from '../api/queries';
import { Folder } from 'lucide-react';

const CategoriesPage = () => {
  const navigate = useNavigate();
  const { data: categories, isLoading } = useCategories();
  const { data: templates } = useTemplates();

  if (isLoading) return <div>Loading categories...</div>;

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Categories</h1>
          <p className="page-subtitle">Browse templates organized by category.</p>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: '16px' }}>
        {categories?.map((cat) => {
          const count = templates?.filter((t) => t.category === cat).length || 0;
          return (
            <div
              key={cat}
              className="card"
              style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '14px' }}
              onClick={() => navigate(`/templates?category=${encodeURIComponent(cat)}`)}
            >
              <div style={{ padding: '10px', backgroundColor: 'var(--accent-soft)', borderRadius: 'var(--radius-md)' }}>
                <Folder size={20} color="var(--accent-primary)" />
              </div>
              <div>
                <h3 style={{ margin: 0, fontSize: '0.95rem' }}>{cat}</h3>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{count} template{count === 1 ? '' : 's'}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default CategoriesPage;
