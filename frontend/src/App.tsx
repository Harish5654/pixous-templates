import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './dashboard/Dashboard';
import TemplatePage from './templates/TemplatePage';
import TemplateEditor from './templates/editor/TemplateEditor';
import CategoriesPage from './templates/CategoriesPage';
import NoticeBoardPage from './templates/NoticeBoardPage';
import DraftsPage from './templates/DraftsPage';
import FavoritesPage from './templates/FavoritesPage';
import RecentPage from './templates/RecentPage';
import ApprovalsPage from './templates/ApprovalsPage';
import MasterDataPage from './admin/MasterDataPage';
import SettingsPage from './settings/SettingsPage';
import NotFoundPage from './components/NotFoundPage';
import LoginPage from './auth/LoginPage';
import { RequireAuth, RequireRole } from './auth/RouteGuards';

function App() {
  return (
    <BrowserRouter>
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
    </BrowserRouter>
  );
}

export default App;
