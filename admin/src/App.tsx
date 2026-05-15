import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { ConfigProvider, theme } from 'antd';
import AdminLayout from './layouts/AdminLayout';
import DashboardPage from './pages/Dashboard';
import ArtistPoolPage from './pages/ArtistPool';
import ContentReviewPage from './pages/ContentReview';
import UsersPage from './pages/Users';
import ModelMonitorPage from './pages/ModelMonitor';
import LoginPage from './pages/Login';

const darkTheme = {
  algorithm: theme.darkAlgorithm,
  token: {
    colorPrimary: '#7c5cfc',
    colorBgContainer: '#1e1e32',
    colorBgElevated: '#1a1a2e',
    colorBgLayout: '#0c0c14',
    colorBorder: 'rgba(255,255,255,0.08)',
    borderRadius: 10,
    colorText: '#f0f0f5',
    colorTextSecondary: '#9ca3af',
  },
};

function RequireAuth({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const token = localStorage.getItem('admin_token');
  if (!token) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }
  return <>{children}</>;
}

function App() {
  return (
    <ConfigProvider theme={darkTheme}>
      <BrowserRouter basename="/admin">
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/" element={<RequireAuth><AdminLayout /></RequireAuth>}>
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard" element={<DashboardPage />} />
            <Route path="artists" element={<ArtistPoolPage />} />
            <Route path="content" element={<ContentReviewPage />} />
            <Route path="users" element={<UsersPage />} />
            <Route path="model-monitor" element={<ModelMonitorPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ConfigProvider>
  );
}

export default App;
