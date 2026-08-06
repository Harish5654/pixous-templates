import { User, Palette, PanelLeft } from 'lucide-react';
import { useUIStore } from '../store/uiStore';
import { useAuthStore } from '../store/authStore';
import Accordion from '../components/Accordion';

const SettingsPage = () => {
  const { sidebarOpen, toggleSidebar } = useUIStore();
  const currentUser = useAuthStore((s) => s.user);

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

export default SettingsPage;
