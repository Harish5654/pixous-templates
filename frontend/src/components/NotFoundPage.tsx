import { useNavigate } from 'react-router-dom';
import { Compass } from 'lucide-react';
import EmptyState from './EmptyState';

const NotFoundPage = () => {
  const navigate = useNavigate();
  return (
    <EmptyState
      icon={Compass}
      title="Page not found"
      description="The page you're looking for doesn't exist or may have been moved."
      actionLabel="Back to Dashboard"
      onAction={() => navigate('/dashboard')}
    />
  );
};

export default NotFoundPage;
