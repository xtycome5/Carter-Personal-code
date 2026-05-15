import { useState } from 'react';
import { Card, Table, Tag, Button, Input, Space, Avatar, Popconfirm, message } from 'antd';
import { SearchOutlined, StopOutlined, CheckCircleOutlined } from '@ant-design/icons';

interface User {
  id: string;
  email: string;
  nickname: string;
  avatarUrl?: string;
  status: 'active' | 'banned';
  dreamsCount: number;
  imagesCount: number;
  videosCount: number;
  createdAt: string;
  lastActive: string;
}

const mockUsers: User[] = [
  { id: 'bc1c4239', email: 'carter@example.com', nickname: 'Carter', status: 'active', dreamsCount: 45, imagesCount: 78, videosCount: 42, createdAt: '2026-05-10', lastActive: '2026-05-15 16:47' },
  { id: 'a1b2c3d4', email: 'alice@gmail.com', nickname: 'Alice', status: 'active', dreamsCount: 12, imagesCount: 24, videosCount: 8, createdAt: '2026-05-12', lastActive: '2026-05-15 14:30' },
  { id: 'e5f6g7h8', email: 'spammer@test.com', nickname: 'BadUser', status: 'banned', dreamsCount: 3, imagesCount: 6, videosCount: 0, createdAt: '2026-05-14', lastActive: '2026-05-14 09:00' },
];

export default function UsersPage() {
  const [users, setUsers] = useState<User[]>(mockUsers);
  const [search, setSearch] = useState('');

  const filteredUsers = users.filter(u =>
    u.email.toLowerCase().includes(search.toLowerCase()) ||
    u.nickname.toLowerCase().includes(search.toLowerCase())
  );

  const toggleBan = (id: string) => {
    setUsers(users.map(u => {
      if (u.id === id) {
        const newStatus = u.status === 'active' ? 'banned' : 'active';
        message.success(`User ${newStatus === 'banned' ? 'banned' : 'unbanned'}`);
        return { ...u, status: newStatus as 'active' | 'banned' };
      }
      return u;
    }));
  };

  const columns = [
    {
      title: 'User',
      key: 'user',
      render: (_: any, record: User) => (
        <Space>
          <Avatar style={{ backgroundColor: '#7c5cfc' }}>{record.nickname[0]}</Avatar>
          <div>
            <div style={{ color: '#f0f0f5', fontSize: 13 }}>{record.nickname}</div>
            <div style={{ color: '#6b7280', fontSize: 11 }}>{record.email}</div>
          </div>
        </Space>
      ),
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (v: string) => (
        <Tag color={v === 'active' ? 'green' : 'red'}>{v}</Tag>
      ),
    },
    {
      title: 'Usage',
      key: 'usage',
      render: (_: any, record: User) => (
        <Space size={12}>
          <span style={{ color: '#9ca3af', fontSize: 12 }}>{record.dreamsCount} dreams</span>
          <span style={{ color: '#9ca3af', fontSize: 12 }}>{record.imagesCount} imgs</span>
          <span style={{ color: '#9ca3af', fontSize: 12 }}>{record.videosCount} vids</span>
        </Space>
      ),
    },
    { title: 'Joined', dataIndex: 'createdAt', key: 'createdAt' },
    { title: 'Last Active', dataIndex: 'lastActive', key: 'lastActive' },
    {
      title: 'Actions',
      key: 'actions',
      render: (_: any, record: User) => (
        <Popconfirm
          title={record.status === 'active' ? 'Ban this user?' : 'Unban this user?'}
          onConfirm={() => toggleBan(record.id)}
        >
          <Button
            size="small"
            icon={record.status === 'active' ? <StopOutlined /> : <CheckCircleOutlined />}
            danger={record.status === 'active'}
          >
            {record.status === 'active' ? 'Ban' : 'Unban'}
          </Button>
        </Popconfirm>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div>
          <h2 style={{ color: '#f0f0f5', margin: 0 }}>用户管理</h2>
          <p style={{ color: '#9ca3af', fontSize: 13, margin: '4px 0 0' }}>
            {users.length} registered users
          </p>
        </div>
        <Input
          prefix={<SearchOutlined />}
          placeholder="Search by email or nickname..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          style={{ width: 260 }}
        />
      </div>

      <Card>
        <Table
          dataSource={filteredUsers}
          columns={columns}
          rowKey="id"
          pagination={{ pageSize: 20 }}
          size="small"
        />
      </Card>
    </div>
  );
}
