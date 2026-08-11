import { useNavigate } from 'react-router-dom';
import { useTemplates } from '../api/queries';
import { Star } from 'lucide-react';
import { useFavoritesStore } from '../store/favoritesStore';
import TemplateCard from '../components/TemplateCard';
import EmptyState from '../components/EmptyState';
import DataError from '../components/DataError';

const FavoritesPage = () => {
  const navigate = useNavigate();
  const { data: templates, isLoading, isError } = useTemplates();
  const { favoriteIds } = useFavoritesStore();

  if (isLoading) return <div>Loading favorites...</div>;
  if (isError) return <DataError message="Couldn't load favorites. Check that the server is running and try again." />;

  const favorites = templates?.filter((t) => favoriteIds.includes(t.id)) || [];

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Favorites</h1>
          <p className="page-subtitle">Templates you've starred for quick access.</p>
        </div>
      </div>

      {favorites.length === 0 ? (
        <EmptyState
          icon={Star}
          title="No favorites yet"
          description="Star any template from the library to pin it here for quick access."
          actionLabel="Browse Templates"
          onAction={() => navigate('/templates')}
        />
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '20px' }}>
          {favorites.map((t) => <TemplateCard key={t.id} template={t} />)}
        </div>
      )}
    </div>
  );
};

export default FavoritesPage;
