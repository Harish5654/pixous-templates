import { lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import { RequireAuth, RequireRole } from './auth/RouteGuards';

// Route-level code splitting: each page is its own chunk, so the initial
// bundle no longer pulls in the editor, dashboard, and every other screen.
const Dashboard = lazy(() => import('./dashboard/Dashboard'));
const TemplatePage = lazy(() => import('./templates/TemplatePage'));
const TemplateEditor = lazy(() => import('./templates/editor/TemplateEditor'));
const CategoriesPage = lazy(() => import('./templates/CategoriesPage'));
const NoticeBoardPage = lazy(() => import('./templates/NoticeBoardPage'));
const DraftsPage = lazy(() => import('./templates/DraftsPage'));
const FavoritesPage = lazy(() => import('./templates/FavoritesPage'));
const RecentPage = lazy(() => import('./templates/RecentPage'));
const ApprovalsPage = lazy(() => import('./templates/ApprovalsPage'));
const MasterDataPage = lazy(() => import('./admin/MasterDataPage'));
const SettingsPage = lazy(() => import('./settings/SettingsPage'));
const NotFoundPage = lazy(() => import('./components/NotFoundPage'));
const LoginPage = lazy(() => import('./auth/LoginPage'));

function PageLoader() {
  return <div style={{ padding: '32px', color: 'var(--text-secondary)' }}>Loading…</div>;
}

function App() {
  return (
    <BrowserRouter>
      <Suspense fallback={<PageLoader />}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />

          <Route element={<RequireAuth />}>
            <Route path="/" element={<Layout />}>
              <Route index element={<Navigate to="/dashboard" replace />} />
              <Route path="dashboard" element={<Dashboard />} />
              <Route path="templates" element={<TemplatePage />} />
              <Route path="templates/categories" element={<CategoriesPage />} />
              <Route path="notice-board" element={<NoticeBoardPage />} />
              <Route element={<RequireRole roles={['Admin', 'Editor']} />}>
                <Route path="templates/new" element={<TemplateEditor />} />
                <Route path="templates/:id/edit" element={<TemplateEditor />} />
              </Route>
              <Route path="drafts" element={<DraftsPage />} />
              <Route path="favorites" element={<FavoritesPage />} />
              <Route path="recent" element={<RecentPage />} />
              <Route path="approvals" element={<ApprovalsPage />} />
              <Route element={<RequireRole roles={['Admin']} />}>
                <Route path="admin/master-data" element={<MasterDataPage />} />
              </Route>
              <Route path="settings" element={<SettingsPage />} />
              <Route path="*" element={<NotFoundPage />} />
            </Route>
          </Route>
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}

export default App;
