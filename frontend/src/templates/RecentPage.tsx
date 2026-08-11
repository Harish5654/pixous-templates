import { useNavigate } from 'react-router-dom';
import { useTemplates } from '../api/queries';
import { Clock } from 'lucide-react';
import { useRecentStore } from '../store/recentStore';
import TemplateCard from '../components/TemplateCard';
import EmptyState from '../components/EmptyState';
import DataError from '../components/DataError';

const RecentPage = () => {
  const navigate = useNavigate();
  const { data: templates, isLoading, isError } = useTemplates();
  const { recentIds } = useRecentStore();

  if (isLoading) return <div>Loading recent templates...</div>;
  if (isError) return <DataError message="Couldn't load recent templates. Check that the server is running and try again." />;

  const recent = recentIds
    .map((id) => templates?.find((t) => t.id === id))
    .filter((t): t is NonNullable<typeof t> => Boolean(t));

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Recent</h1>
          <p className="page-subtitle">Templates you've recently opened in the editor.</p>
        </div>
      </div>

      {recent.length === 0 ? (
        <EmptyState
          icon={Clock}
          title="Nothing opened yet"
          description="Templates you open in the editor will show up here for quick access."
          actionLabel="Browse Templates"
          onAction={() => navigate('/templates')}
        />
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '20px' }}>
          {recent.map((t) => <TemplateCard key={t.id} template={t} />)}
        </div>
      )}
    </div>
  );
};

export default RecentPage;
