import { useState } from 'react';
import { Card, Table, Button, Tag, Space, Image, Tabs, Badge, message } from 'antd';
import { CheckOutlined, CloseOutlined, StarOutlined, StarFilled } from '@ant-design/icons';

interface Generation {
  id: string;
  type: 'image' | 'video';
  user: string;
  dreamTitle: string;
  resultUrl: string;
  status: 'pending_review' | 'approved' | 'rejected' | 'featured';
  createdAt: string;
}

const mockData: Generation[] = [
  { id: '71194129', type: 'video', user: 'carter', dreamTitle: '星空下的海洋', resultUrl: 'https://dream-recorder-media.oss-ap-southeast-5.aliyuncs.com/videos/bc1c4239/71194129.mp4', status: 'pending_review', createdAt: '2026-05-15 16:47' },
  { id: 'b7cf5e0d', type: 'image', user: 'carter', dreamTitle: '星空下的海洋', resultUrl: 'https://dream-recorder-media.oss-ap-southeast-5.aliyuncs.com/images/bc1c4239/b7cf5e0d.png', status: 'approved', createdAt: '2026-05-15 16:46' },
  { id: '890ebf60', type: 'image', user: 'carter', dreamTitle: '飞翔的城市', resultUrl: 'https://dream-recorder-media.oss-ap-southeast-5.aliyuncs.com/images/bc1c4239/890ebf60.png', status: 'featured', createdAt: '2026-05-15 16:33' },
  { id: '64eb837c', type: 'video', user: 'carter', dreamTitle: '深海珊瑚', resultUrl: '', status: 'rejected', createdAt: '2026-05-15 16:26' },
  { id: 'a9aeadea', type: 'image', user: 'carter', dreamTitle: '深海珊瑚', resultUrl: 'https://dream-recorder-media.oss-ap-southeast-5.aliyuncs.com/images/bc1c4239/a9aeadea.png', status: 'pending_review', createdAt: '2026-05-15 16:25' },
];

export default function ContentReviewPage() {
  const [data, setData] = useState<Generation[]>(mockData);
  const [tab, setTab] = useState('all');

  const filteredData = tab === 'all' ? data :
    tab === 'pending' ? data.filter(d => d.status === 'pending_review') :
    tab === 'featured' ? data.filter(d => d.status === 'featured') :
    data;

  const updateStatus = (id: string, status: Generation['status']) => {
    setData(data.map(d => d.id === id ? { ...d, status } : d));
    message.success(`Status updated to ${status}`);
  };

  const statusColors: Record<string, string> = {
    pending_review: 'orange',
    approved: 'green',
    rejected: 'red',
    featured: 'gold',
  };

  const columns = [
    {
      title: 'Preview',
      dataIndex: 'resultUrl',
      key: 'preview',
      width: 80,
      render: (url: string, record: Generation) => (
        url && record.type === 'image' ? (
          <Image src={url} width={60} height={60} style={{ objectFit: 'cover', borderRadius: 6 }} />
        ) : (
          <div style={{ width: 60, height: 60, background: '#1a1a2e', borderRadius: 6, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 10, color: '#6b7280' }}>
            {record.type === 'video' ? '▶' : '—'}
          </div>
        )
      ),
    },
    { title: 'Dream', dataIndex: 'dreamTitle', key: 'dreamTitle' },
    {
      title: 'Type',
      dataIndex: 'type',
      key: 'type',
      render: (v: string) => <Tag color={v === 'image' ? 'purple' : 'blue'}>{v}</Tag>,
    },
    { title: 'User', dataIndex: 'user', key: 'user' },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (v: string) => <Tag color={statusColors[v]}>{v.replace('_', ' ')}</Tag>,
    },
    { title: 'Created', dataIndex: 'createdAt', key: 'createdAt' },
    {
      title: 'Actions',
      key: 'actions',
      render: (_: any, record: Generation) => (
        <Space>
          {record.status !== 'approved' && record.status !== 'featured' && (
            <Button size="small" icon={<CheckOutlined />} onClick={() => updateStatus(record.id, 'approved')}>
              Approve
            </Button>
          )}
          {record.status !== 'rejected' && (
            <Button size="small" icon={<CloseOutlined />} danger onClick={() => updateStatus(record.id, 'rejected')}>
              Reject
            </Button>
          )}
          {record.status === 'approved' && (
            <Button size="small" icon={<StarOutlined />} style={{ color: '#faad14' }} onClick={() => updateStatus(record.id, 'featured')}>
              Feature
            </Button>
          )}
          {record.status === 'featured' && (
            <Button size="small" icon={<StarFilled />} style={{ color: '#faad14' }} onClick={() => updateStatus(record.id, 'approved')}>
              Unfeature
            </Button>
          )}
        </Space>
      ),
    },
  ];

  const pendingCount = data.filter(d => d.status === 'pending_review').length;
  const featuredCount = data.filter(d => d.status === 'featured').length;

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <h2 style={{ color: '#f0f0f5', margin: 0 }}>内容审核 / Daily Top 20</h2>
        <p style={{ color: '#9ca3af', fontSize: 13, margin: '4px 0 0' }}>
          审核生成内容，精选作品加入 Daily Top 20 展示
        </p>
      </div>

      <Card>
        <Tabs
          activeKey={tab}
          onChange={setTab}
          items={[
            { key: 'all', label: 'All' },
            { key: 'pending', label: <Badge count={pendingCount} size="small" offset={[8, 0]}>Pending</Badge> },
            { key: 'featured', label: <span><StarFilled style={{ color: '#faad14' }} /> Featured ({featuredCount})</span> },
          ]}
        />
        <Table
          dataSource={filteredData}
          columns={columns}
          rowKey="id"
          pagination={{ pageSize: 10 }}
          size="small"
        />
      </Card>
    </div>
  );
}
