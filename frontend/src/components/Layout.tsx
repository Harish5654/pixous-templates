import React, { useEffect, useMemo, useRef, useState } from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard, FileText, Settings, LogOut, Search, User,
  Folder, FileEdit, ClipboardCheck, Star, Clock, PanelLeft, Database
} from 'lucide-react';
import { useUIStore } from '../store/uiStore';
import { useAuthStore } from '../store/authStore';
import { useTemplates } from '../api/queries';
import type { Role } from '../types/user';

const NAV_ITEMS: { to: string; label: string; icon: typeof LayoutDashboard; end: boolean; roles?: Role[] }[] = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: '/templates', label: 'Templates', icon: FileText, end: true },
  { to: '/templates/categories', label: 'Categories', icon: Folder, end: true },
  { to: '/drafts', label: 'Drafts', icon: FileEdit, end: true },
  { to: '/approvals', label: 'Approvals', icon: ClipboardCheck, end: true },
  { to: '/favorites', label: 'Favorites', icon: Star, end: true },
  { to: '/recent', label: 'Recent', icon: Clock, end: true },
  { to: '/admin/master-data', label: 'Master Data', icon: Database, end: true, roles: ['Admin'] },
];

const Layout = () => {
  const { sidebarOpen, toggleSidebar } = useUIStore();
  const currentUser = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const { data: templates } = useTemplates();
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [searchFocused, setSearchFocused] = useState(false);
  const searchRef = useRef<HTMLFormElement>(null);

  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(e.target as Node)) setSearchFocused(false);
    };
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  // Auto-collapse the sidebar when the window shrinks past the responsive
  // breakpoint (mobile/tablet). Only collapses — never forces expansion.
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth < 900 && useUIStore.getState().sidebarOpen) {
        useUIStore.getState().toggleSidebar();
      }
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const results = useMemo(() => {
    if (!query.trim() || !templates) return [];
    const q = query.toLowerCase();
    return templates.filter((t) =>
      t.name.toLowerCase().includes(q) ||
      t.category.toLowerCase().includes(q) ||
      t.owner.toLowerCase().includes(q) ||
      t.tags?.some((tag) => tag.toLowerCase().includes(q))
    ).slice(0, 6);
  }, [query, templates]);

  const canAuthor = currentUser?.role === 'Admin' || currentUser?.role === 'Editor';

  const goToTemplate = (id: string, name: string) => {
    setQuery('');
    setSearchFocused(false);
    navigate(canAuthor ? `/templates/${id}/edit` : `/templates?q=${encodeURIComponent(name)}`);
  };

  const submitSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    setSearchFocused(false);
    navigate(`/templates?q=${encodeURIComponent(query.trim())}`);
  };

  return (
    <div className="app-container">
      {/* Sidebar */}
      <aside className={`sidebar ${sidebarOpen ? '' : 'collapsed'}`}>
        <div className="sidebar-header">
          {sidebarOpen ? (
            <img src="/pixous_logo.png" alt="Pixous Technologies" style={{ height: '50px', objectFit: 'contain' }} />
          ) : (
            <div style={{ width: '28px', height: '28px', borderRadius: '8px', backgroundColor: '#173F5F', color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700, fontSize: '0.85rem', margin: '0 auto' }}>
              P
            </div>
          )}
          {sidebarOpen && (
            <button className="icon-btn" onClick={toggleSidebar} title="Collapse sidebar">
              <PanelLeft size={18} />
            </button>
          )}
        </div>
        {!sidebarOpen && (
          <div style={{ display: 'flex', justifyContent: 'center', padding: '8px 0' }}>
            <button className="icon-btn" onClick={toggleSidebar} title="Expand sidebar">
              <PanelLeft size={18} />
            </button>
          </div>
        )}

        <nav className="sidebar-nav">
          {NAV_ITEMS.filter(({ roles }) => !roles || (currentUser && roles.includes(currentUser.role))).map(({ to, label, icon: Icon, end }) => (
            <NavLink key={to} to={to} end={end} title={label} className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
              <Icon />
              {sidebarOpen && <span>{label}</span>}
            </NavLink>
          ))}
        </nav>

        <div style={{ padding: '8px 12px' }}>
          <NavLink to="/settings" end title="Settings" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            <Settings />
            {sidebarOpen && <span>Settings</span>}
          </NavLink>
        </div>

        <div className="sidebar-header" style={{ borderTop: '1px solid var(--border-color)', borderBottom: 'none' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '0.9rem', minWidth: 0 }}>
            <div style={{ width: '32px', height: '32px', borderRadius: '50%', backgroundColor: 'var(--accent-soft)', color: 'var(--accent-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
              <User size={16} />
            </div>
            {sidebarOpen && (
              <div style={{ display: 'flex', flexDirection: 'column', minWidth: 0 }}>
                <span style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{currentUser?.name}</span>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{currentUser?.role}</span>
              </div>
            )}
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="main-content">
        <header className="topbar">
          <form onSubmit={submitSearch} ref={searchRef} style={{ position: 'relative', flex: 1, maxWidth: '440px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', backgroundColor: 'var(--bg-hover)', borderRadius: 'var(--radius-sm)', padding: '9px 14px' }}>
              <Search size={16} color="var(--text-tertiary)" />
              <input
                type="text"
                placeholder="Search templates, categories, owners..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onFocus={() => setSearchFocused(true)}
                style={{ background: 'transparent', border: 'none', color: 'var(--text-primary)', outline: 'none', width: '100%', fontSize: '0.9rem' }}
              />
            </div>
            {searchFocused && results.length > 0 && (
              <div className="search-dropdown">
                {results.map((t) => (
                  <div key={t.id} className="search-dropdown-item" onClick={() => goToTemplate(t.id, t.name)}>
                    <span style={{ fontWeight: 500 }}>{t.name}</span>
                    <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>{t.category} · {t.owner}</span>
                  </div>
                ))}
              </div>
            )}
          </form>

          <button className="btn btn-outline" style={{ display: 'flex', alignItems: 'center', gap: '8px' }} onClick={() => { logout(); navigate('/login'); }}>
            <LogOut size={16} /> Logout
          </button>
        </header>

        <div className="content-area">
          <Outlet />
        </div>
      </main>
    </div>
  );
};

export default Layout;
