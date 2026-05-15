import { useEffect, useState } from 'react';
import { Card, Row, Col, Statistic, Table, Tag, Spin } from 'antd';
import {
  PictureOutlined,
  VideoCameraOutlined,
  UserOutlined,
  FireOutlined,
} from '@ant-design/icons';
import { adminAPI } from '../lib/api';

export default function DashboardPage() {
  const [stats, setStats] = useState<any>(null);
  const [recent, setRecent] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      adminAPI.getStats(),
      adminAPI.getRecentGenerations(),
    ]).then(([s, r]) => {
      setStats(s);
      setRecent(r.generations || []);
    }).catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id', render: (v: string) => v.slice(0, 8) },
    {
      title: 'Type', dataIndex: 'type', key: 'type',
      render: (v: string) => (
        <Tag color={v === 'image' ? 'purple' : 'blue'}>
          {v === 'image' ? <PictureOutlined /> : <VideoCameraOutlined />} {v}
        </Tag>
      ),
    },
    { title: 'User', dataIndex: 'user', key: 'user' },
    {
      title: 'Status', dataIndex: 'status', key: 'status',
      render: (v: string) => (
        <Tag color={v === 'completed' ? 'green' : v === 'failed' ? 'red' : 'orange'}>{v}</Tag>
      ),
    },
    { title: 'Created', dataIndex: 'created_at', key: 'created_at', render: (v: string) => v ? new Date(v).toLocaleString() : '-' },
  ];

  if (loading) return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;

  return (
    <div>
      <h2 style={{ color: '#f0f0f5', marginBottom: 24 }}>Dashboard</h2>

      <Row gutter={[16, 16]}>
        <Col span={6}>
          <Card>
            <Statistic title="Total Users" value={stats?.total_users || 0} prefix={<UserOutlined />} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="Total Images" value={stats?.total_images || 0} prefix={<PictureOutlined />} valueStyle={{ color: '#7c5cfc' }} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="Total Videos" value={stats?.total_videos || 0} prefix={<VideoCameraOutlined />} valueStyle={{ color: '#3b82f6' }} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="Success Rate" value={stats?.success_rate || 0} suffix="%" prefix={<FireOutlined />} valueStyle={{ color: '#10b981' }} />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col span={12}>
          <Card>
            <Statistic title="Total Dreams" value={stats?.total_dreams || 0} />
          </Card>
        </Col>
        <Col span={12}>
          <Card>
            <Statistic title="Failed" value={stats?.failed || 0} valueStyle={{ color: '#ef4444' }} />
          </Card>
        </Col>
      </Row>

      <Card title="Recent Generations" style={{ marginTop: 24 }}>
        <Table
          dataSource={recent}
          columns={columns}
          rowKey="id"
          pagination={false}
          size="small"
        />
      </Card>
    </div>
  );
}
