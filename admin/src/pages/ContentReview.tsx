import { useEffect, useState } from 'react';
import { Card, Table, Tag, Image, Tabs, Spin } from 'antd';
import { PictureOutlined, VideoCameraOutlined } from '@ant-design/icons';
import { adminAPI } from '../lib/api';

export default function ContentReviewPage() {
  const [data, setData] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState<string | undefined>(undefined);
  const [typeFilter] = useState<string | undefined>(undefined);

  const fetchData = (p: number, status?: string, type?: string) => {
    setLoading(true);
    adminAPI.listGenerations({ page: p, status, gen_type: type })
      .then(res => {
        setData(res.generations || []);
        setTotal(res.total || 0);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchData(1); }, []);

  const handleTabChange = (key: string) => {
    const s = key === 'all' ? undefined : key;
    setStatusFilter(s);
    setPage(1);
    fetchData(1, s, typeFilter);
  };

  const columns = [
    {
      title: 'Preview',
      dataIndex: 'result_url',
      key: 'preview',
      width: 80,
      render: (url: string, record: any) => (
        url && record.type === 'image' ? (
          <Image src={url} width={60} height={60} style={{ objectFit: 'cover', borderRadius: 6 }} />
        ) : (
          <div style={{ width: 60, height: 60, background: '#1a1a2e', borderRadius: 6, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 10, color: '#6b7280' }}>
            {record.type === 'video' ? '▶' : '—'}
          </div>
        )
      ),
    },
    { title: 'Dream', dataIndex: 'dream_title', key: 'dream_title', ellipsis: true },
    {
      title: 'Type',
      dataIndex: 'type',
      key: 'type',
      render: (v: string) => (
        <Tag color={v === 'image' ? 'purple' : 'blue'}>
          {v === 'image' ? <PictureOutlined /> : <VideoCameraOutlined />} {v}
        </Tag>
      ),
    },
    { title: 'User', dataIndex: 'user', key: 'user' },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (v: string) => {
        const colors: Record<string, string> = { completed: 'green', failed: 'red', processing: 'orange', pending: 'default' };
        return <Tag color={colors[v] || 'default'}>{v}</Tag>;
      },
    },
    {
      title: 'Created',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (v: string) => v ? new Date(v).toLocaleString() : '-',
    },
  ];

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <h2 style={{ color: '#f0f0f5', margin: 0 }}>内容审核</h2>
        <p style={{ color: '#9ca3af', fontSize: 13, margin: '4px 0 0' }}>
          {total} total generations
        </p>
      </div>

      <Card>
        <Tabs
          onChange={handleTabChange}
          items={[
            { key: 'all', label: 'All' },
            { key: 'completed', label: 'Completed' },
            { key: 'failed', label: 'Failed' },
            { key: 'processing', label: 'Processing' },
          ]}
        />
        <Spin spinning={loading}>
          <Table
            dataSource={data}
            columns={columns}
            rowKey="id"
            pagination={{
              current: page,
              total,
              pageSize: 20,
              onChange: (p) => { setPage(p); fetchData(p, statusFilter, typeFilter); },
            }}
            size="small"
          />
        </Spin>
      </Card>
    </div>
  );
}
