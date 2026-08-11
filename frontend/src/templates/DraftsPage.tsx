import { useNavigate } from 'react-router-dom';
import { useTemplates } from '../api/queries';
import { FileEdit } from 'lucide-react';
import TemplateCard from '../components/TemplateCard';
import EmptyState from '../components/EmptyState';
import DataError from '../components/DataError';

const DraftsPage = () => {
  const navigate = useNavigate();
  const { data: templates, isLoading, isError } = useTemplates();

  if (isLoading) return <div>Loading drafts...</div>;
  if (isError) return <DataError message="Couldn't load drafts. Check that the server is running and try again." />;

  const drafts = templates?.filter((t) => t.status === 'Draft') || [];

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Drafts</h1>
          <p className="page-subtitle">Templates in progress that haven't been published yet.</p>
        </div>
      </div>

      {drafts.length === 0 ? (
        <EmptyState
          icon={FileEdit}
          title="No drafts right now"
          description="Templates you save without publishing will show up here."
          actionLabel="Browse Templates"
          onAction={() => navigate('/templates')}
        />
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '20px' }}>
          {drafts.map((t) => <TemplateCard key={t.id} template={t} />)}
        </div>
      )}
    </div>
  );
};

export default DraftsPage;
