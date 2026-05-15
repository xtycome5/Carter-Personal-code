import { useEffect, useState } from 'react';
import { Card, Table, Tag, Spin } from 'antd';
import { adminAPI } from '../lib/api';

export default function ArtistPoolPage() {
  const [artists, setArtists] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    adminAPI.listArtists()
      .then(res => setArtists(res.artists || []))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const columns = [
    { title: 'Artist', dataIndex: 'name', key: 'name' },
    {
      title: 'Category',
      dataIndex: 'category',
      key: 'category',
      render: (v: string) => <Tag>{v}</Tag>,
    },
    {
      title: 'Style Description',
      dataIndex: 'style',
      key: 'style',
      ellipsis: true,
      width: 400,
    },
  ];

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <h2 style={{ color: '#f0f0f5', margin: 0 }}>画家池管理</h2>
        <p style={{ color: '#9ca3af', fontSize: 13, margin: '4px 0 0' }}>
          {artists.length} artists — 每次生图随机取 3 位
        </p>
      </div>

      <Card>
        <Spin spinning={loading}>
          <Table
            dataSource={artists}
            columns={columns}
            rowKey="name"
            pagination={false}
            size="small"
          />
        </Spin>
      </Card>
    </div>
  );
}
