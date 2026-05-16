import { useEffect, useState } from 'react';
import { Card, Table, Tag, Image, Tabs, Spin, Tooltip } from 'antd';
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
      width: 90,
      render: (v: string) => (
        <Tag color={v === 'image' ? 'purple' : 'blue'}>
          {v === 'image' ? <PictureOutlined /> : <VideoCameraOutlined />} {v}
        </Tag>
      ),
    },
    {
      title: 'Mode',
      key: 'mode',
      width: 90,
      render: (_: any, record: any) => {
        const mode = record.metadata?.mode;
        if (!mode) return <span style={{ color: '#6b7280' }}>—</span>;
        const modeColors: Record<string, string> = {
          artist_ref: 'geekblue',
          t2i: 'cyan',
          v2i: 'magenta',
          r2v: 'volcano',
        };
        return <Tag color={modeColors[mode] || 'default'}>{mode}</Tag>;
      },
    },
    {
      title: 'Artist Ref',
      key: 'artist_ref',
      width: 70,
      render: (_: any, record: any) => {
        const refUrl = record.metadata?.artist_reference;
        if (!refUrl) return <span style={{ color: '#6b7280' }}>—</span>;
        return (
          <Tooltip title={refUrl.split('/artists/')[1] || refUrl}>
            <Image
              src={refUrl}
              width={40}
              height={40}
              style={{ objectFit: 'cover', borderRadius: 4 }}
              fallback="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHJlY3Qgd2lkdGg9IjQwIiBoZWlnaHQ9IjQwIiBmaWxsPSIjMmEyYTNlIi8+PC9zdmc+"
            />
          </Tooltip>
        );
      },
    },
    { title: 'User', dataIndex: 'user', key: 'user', width: 100 },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (v: string) => {
        const colors: Record<string, string> = { completed: 'green', failed: 'red', processing: 'orange', pending: 'default' };
        return <Tag color={colors[v] || 'default'}>{v}</Tag>;
      },
    },
    {
      title: 'Prompt',
      dataIndex: 'prompt',
      key: 'prompt',
      ellipsis: true,
      width: 200,
      render: (v: string) => (
        <Tooltip title={v}>
          <span style={{ fontSize: 11, color: '#9ca3af' }}>{v}</span>
        </Tooltip>
      ),
    },
    {
      title: 'Created',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 150,
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
            scroll={{ x: 900 }}
          />
        </Spin>
      </Card>
    </div>
  );
}
