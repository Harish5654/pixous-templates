import { ClipboardCheck } from 'lucide-react';
import EmptyState from '../components/EmptyState';

const ApprovalsPage = () => {
  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Approvals</h1>
          <p className="page-subtitle">Review and sign off on templates before they go live.</p>
        </div>
      </div>

      <EmptyState
        icon={ClipboardCheck}
        title="Approvals workflow coming soon"
        description="Once enabled, templates awaiting sign-off from a reviewer will appear here for approval before publishing."
      />
    </div>
  );
};

export default ApprovalsPage;
