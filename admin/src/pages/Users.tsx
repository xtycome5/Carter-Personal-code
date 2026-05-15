import { useEffect, useState } from 'react';
import { Card, Table, Tag, Input, Space, Avatar, Spin } from 'antd';
import { SearchOutlined } from '@ant-design/icons';
import { adminAPI } from '../lib/api';

export default function UsersPage() {
  const [users, setUsers] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);

  const fetchUsers = (p: number, s: string) => {
    setLoading(true);
    adminAPI.listUsers({ page: p, search: s || undefined })
      .then(res => {
        setUsers(res.users || []);
        setTotal(res.total || 0);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchUsers(1, ''); }, []);

  const handleSearch = (value: string) => {
    setSearch(value);
    setPage(1);
    fetchUsers(1, value);
  };

  const columns = [
    {
      title: 'User',
      key: 'user',
      render: (_: any, record: any) => (
        <Space>
          <Avatar style={{ backgroundColor: '#7c5cfc' }}>{(record.nickname || '?')[0]}</Avatar>
          <div>
            <div style={{ color: '#f0f0f5', fontSize: 13 }}>{record.nickname}</div>
            <div style={{ color: '#6b7280', fontSize: 11 }}>{record.email}</div>
          </div>
        </Space>
      ),
    },
    {
      title: 'Provider',
      dataIndex: 'oauth_provider',
      key: 'oauth_provider',
      render: (v: string) => v ? <Tag>{v}</Tag> : <Tag color="default">email</Tag>,
    },
    {
      title: 'Usage',
      key: 'usage',
      render: (_: any, record: any) => (
        <Space size={12}>
          <span style={{ color: '#9ca3af', fontSize: 12 }}>{record.dreams_count} dreams</span>
          <span style={{ color: '#9ca3af', fontSize: 12 }}>{record.images_count} imgs</span>
          <span style={{ color: '#9ca3af', fontSize: 12 }}>{record.videos_count} vids</span>
        </Space>
      ),
    },
    {
      title: 'Joined',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (v: string) => v ? new Date(v).toLocaleDateString() : '-',
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div>
          <h2 style={{ color: '#f0f0f5', margin: 0 }}>用户管理</h2>
          <p style={{ color: '#9ca3af', fontSize: 13, margin: '4px 0 0' }}>
            {total} registered users
          </p>
        </div>
        <Input.Search
          prefix={<SearchOutlined />}
          placeholder="Search by email or nickname..."
          onSearch={handleSearch}
          style={{ width: 280 }}
          allowClear
        />
      </div>

      <Card>
        <Spin spinning={loading}>
          <Table
            dataSource={users}
            columns={columns}
            rowKey="id"
            pagination={{
              current: page,
              total,
              pageSize: 20,
              onChange: (p) => { setPage(p); fetchUsers(p, search); },
            }}
            size="small"
          />
        </Spin>
      </Card>
    </div>
  );
}
