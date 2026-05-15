import { Card, Row, Col, Statistic, Table, Tag } from 'antd';
import {
  PictureOutlined,
  VideoCameraOutlined,
  UserOutlined,
  CloudOutlined,
} from '@ant-design/icons';

export default function DashboardPage() {
  // TODO: fetch from API
  const stats = {
    totalUsers: 12,
    totalDreams: 87,
    totalImages: 156,
    totalVideos: 89,
    ossUsageMB: 2340,
    successRate: 94.2,
  };

  const recentGenerations = [
    { id: '71194129', type: 'video', user: 'carter', status: 'completed', created: '2026-05-15 16:47' },
    { id: 'b7cf5e0d', type: 'image', user: 'carter', status: 'completed', created: '2026-05-15 16:46' },
    { id: '36be195f', type: 'video', user: 'carter', status: 'completed', created: '2026-05-15 16:34' },
    { id: '890ebf60', type: 'image', user: 'carter', status: 'completed', created: '2026-05-15 16:33' },
    { id: '64eb837c', type: 'video', user: 'carter', status: 'failed', created: '2026-05-15 16:26' },
  ];

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
      render: (v: string) => <Tag color={v === 'completed' ? 'green' : 'red'}>{v}</Tag>,
    },
    { title: 'Created', dataIndex: 'created', key: 'created' },
  ];

  return (
    <div>
      <h2 style={{ color: '#f0f0f5', marginBottom: 24 }}>Dashboard</h2>

      <Row gutter={[16, 16]}>
        <Col span={6}>
          <Card>
            <Statistic title="Total Users" value={stats.totalUsers} prefix={<UserOutlined />} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="Total Images" value={stats.totalImages} prefix={<PictureOutlined />} valueStyle={{ color: '#7c5cfc' }} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="Total Videos" value={stats.totalVideos} prefix={<VideoCameraOutlined />} valueStyle={{ color: '#3b82f6' }} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="OSS Storage" value={stats.ossUsageMB} suffix="MB" prefix={<CloudOutlined />} />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col span={12}>
          <Card>
            <Statistic title="Success Rate" value={stats.successRate} suffix="%" valueStyle={{ color: '#10b981' }} />
          </Card>
        </Col>
        <Col span={12}>
          <Card>
            <Statistic title="Total Dreams" value={stats.totalDreams} />
          </Card>
        </Col>
      </Row>

      <Card title="Recent Generations" style={{ marginTop: 24 }}>
        <Table
          dataSource={recentGenerations}
          columns={columns}
          rowKey="id"
          pagination={false}
          size="small"
        />
      </Card>
    </div>
  );
}
