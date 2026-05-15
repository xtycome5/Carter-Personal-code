import { useState } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { Layout, Menu } from 'antd';
import {
  DashboardOutlined,
  PictureOutlined,
  AuditOutlined,
  UserOutlined,
  MonitorOutlined,
} from '@ant-design/icons';

const { Sider, Content, Header } = Layout;

const menuItems = [
  { key: '/dashboard', icon: <DashboardOutlined />, label: 'Dashboard' },
  { key: '/artists', icon: <PictureOutlined />, label: '画家池管理' },
  { key: '/content', icon: <AuditOutlined />, label: '内容审核' },
  { key: '/users', icon: <UserOutlined />, label: '用户管理' },
  { key: '/model-monitor', icon: <MonitorOutlined />, label: '模型监控' },
];

export default function AdminLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        style={{ background: '#14141f' }}
        width={220}
      >
        <div style={{ padding: '20px 16px', textAlign: 'center' }}>
          <h2 style={{
            color: '#7c5cfc',
            fontSize: collapsed ? 14 : 18,
            fontWeight: 700,
            margin: 0,
            whiteSpace: 'nowrap',
          }}>
            {collapsed ? 'DR' : 'Dream Recorder'}
          </h2>
          <p style={{
            color: '#6b7280',
            fontSize: 11,
            margin: '4px 0 0',
            display: collapsed ? 'none' : 'block',
          }}>
            Admin Panel
          </p>
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
          style={{ background: 'transparent', borderRight: 'none' }}
        />
      </Sider>
      <Layout>
        <Header style={{
          background: '#14141f',
          padding: '0 24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'flex-end',
          borderBottom: '1px solid rgba(255,255,255,0.06)',
        }}>
          <span style={{ color: '#9ca3af', fontSize: 13 }}>Admin</span>
        </Header>
        <Content style={{ margin: 24, minHeight: 'auto' }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
}
