import { useEffect, useState } from 'react';
import { Card, Button, Tag, Spin, Modal, Form, Input, Select, Switch, message, Popconfirm, Image } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, PictureOutlined } from '@ant-design/icons';
import { adminAPI } from '../lib/api';

const { TextArea } = Input;

const CATEGORIES = [
  { value: 'surrealism_core', label: '超现实主义核心' },
  { value: 'expressionism', label: '表现主义/情绪扭曲' },
  { value: 'poetic_weightless', label: '诗意梦幻/失重' },
  { value: 'mystical_symbolism', label: '神秘/象征主义' },
  { value: 'modern_dream', label: '现代梦境' },
];

interface Artist {
  id: string;
  key: string;
  name: string;
  style: string;
  masterwork_url?: string;
  painting?: string;
  category?: string;
  active: boolean;
  sort_order: number;
  created_at?: string;
}

export default function ArtistPoolPage() {
  const [artists, setArtists] = useState<Artist[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingArtist, setEditingArtist] = useState<Artist | null>(null);
  const [form] = Form.useForm();

  const loadArtists = () => {
    setLoading(true);
    adminAPI.listArtists()
      .then(res => setArtists(res.artists || []))
      .catch(err => message.error(err.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => { loadArtists(); }, []);

  const openCreate = () => {
    setEditingArtist(null);
    form.resetFields();
    form.setFieldsValue({ active: true, sort_order: 0 });
    setModalOpen(true);
  };

  const openEdit = (artist: Artist) => {
    setEditingArtist(artist);
    form.setFieldsValue(artist);
    setModalOpen(true);
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      if (editingArtist) {
        await adminAPI.updateArtist(editingArtist.id, values);
        message.success(`Updated: ${values.name}`);
      } else {
        await adminAPI.createArtist(values);
        message.success(`Created: ${values.name}`);
      }
      setModalOpen(false);
      loadArtists();
    } catch (err: any) {
      if (err.message) message.error(err.message);
    }
  };

  const handleDelete = async (artist: Artist) => {
    try {
      await adminAPI.deleteArtist(artist.id);
      message.success(`Deactivated: ${artist.name}`);
      loadArtists();
    } catch (err: any) {
      message.error(err.message);
    }
  };

  // 按 category 分组
  const grouped = artists.reduce<Record<string, Artist[]>>((acc, a) => {
    const cat = a.category || 'uncategorized';
    if (!acc[cat]) acc[cat] = [];
    acc[cat].push(a);
    return acc;
  }, {});

  const getCategoryLabel = (key: string) =>
    CATEGORIES.find(c => c.value === key)?.label || key;

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div>
          <h2 style={{ color: '#f0f0f5', margin: 0 }}>画家池管理</h2>
          <p style={{ color: '#9ca3af', fontSize: 13, margin: '4px 0 0' }}>
            {artists.length} 位画家 — 每次生图随机取 3 位作为美学基底
          </p>
        </div>
        <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>
          添加画家
        </Button>
      </div>

      <Spin spinning={loading}>
        {Object.entries(grouped).map(([category, items]) => (
          <div key={category} style={{ marginBottom: 32 }}>
            <h3 style={{ color: '#d1d5db', fontSize: 14, marginBottom: 12 }}>
              {getCategoryLabel(category)}
              <Tag style={{ marginLeft: 8 }}>{items.length}</Tag>
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 16 }}>
              {items.map(artist => (
                <Card
                  key={artist.id}
                  size="small"
                  style={{ borderColor: artist.active ? undefined : '#ff4d4f33' }}
                  actions={[
                    <EditOutlined key="edit" onClick={() => openEdit(artist)} />,
                    <Popconfirm
                      key="del"
                      title="确定停用该画家？"
                      description="停用后不再参与随机选取，可重新激活。"
                      onConfirm={() => handleDelete(artist)}
                    >
                      <DeleteOutlined style={{ color: '#ff4d4f' }} />
                    </Popconfirm>,
                  ]}
                >
                  {/* 参考图 */}
                  <div style={{ marginBottom: 12, textAlign: 'center', background: '#1a1a2e', borderRadius: 8, padding: 8 }}>
                    {artist.masterwork_url ? (
                      <Image
                        src={artist.masterwork_url}
                        alt={artist.name}
                        style={{ maxHeight: 140, objectFit: 'contain', borderRadius: 4 }}
                        fallback="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgdmlld0JveD0iMCAwIDEwMCAxMDAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHJlY3Qgd2lkdGg9IjEwMCIgaGVpZ2h0PSIxMDAiIGZpbGw9IiMyYTJhM2UiLz48dGV4dCB4PSI1MCIgeT0iNTUiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGZpbGw9IiM2NjYiIGZvbnQtc2l6ZT0iMTIiPk5vIEltYWdlPC90ZXh0Pjwvc3ZnPg=="
                      />
                    ) : (
                      <div style={{ height: 100, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        <PictureOutlined style={{ fontSize: 32, color: '#555' }} />
                      </div>
                    )}
                  </div>

                  {/* 信息 */}
                  <Card.Meta
                    title={
                      <span style={{ fontSize: 14 }}>
                        {artist.name}
                        {!artist.active && <Tag color="red" style={{ marginLeft: 6 }}>停用</Tag>}
                      </span>
                    }
                    description={
                      <div>
                        <div style={{ fontSize: 11, color: '#9ca3af', marginBottom: 4 }}>
                          KEY: {artist.key} | {artist.painting || '—'}
                        </div>
                        <div style={{ fontSize: 12, color: '#d1d5db', lineHeight: '1.4', maxHeight: 56, overflow: 'hidden' }}>
                          {artist.style}
                        </div>
                      </div>
                    }
                  />
                </Card>
              ))}
            </div>
          </div>
        ))}
      </Spin>

      {/* 新增/编辑 Modal */}
      <Modal
        title={editingArtist ? `编辑: ${editingArtist.name}` : '添加画家'}
        open={modalOpen}
        onOk={handleSubmit}
        onCancel={() => setModalOpen(false)}
        width={600}
        okText={editingArtist ? '保存' : '创建'}
      >
        <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <Form.Item name="key" label="Key (唯一标识)" rules={[{ required: true }]}>
              <Input placeholder="DALI" disabled={!!editingArtist} />
            </Form.Item>
            <Form.Item name="name" label="画家名" rules={[{ required: true }]}>
              <Input placeholder="Salvador Dalí" />
            </Form.Item>
          </div>

          <Form.Item name="style" label="风格描述 (用于 System Prompt)" rules={[{ required: true }]}>
            <TextArea rows={3} placeholder="melting forms, warped time-space, impossibly detailed renderings..." />
          </Form.Item>

          <Form.Item name="masterwork_url" label="参考图 URL (OSS)">
            <Input placeholder="https://dream-recorder-media.oss-ap-southeast-5.aliyuncs.com/artists/..." />
          </Form.Item>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <Form.Item name="painting" label="代表作">
              <Input placeholder="The Persistence of Memory" />
            </Form.Item>
            <Form.Item name="category" label="分类">
              <Select options={CATEGORIES} placeholder="选择分类" allowClear />
            </Form.Item>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <Form.Item name="sort_order" label="排序">
              <Input type="number" />
            </Form.Item>
            <Form.Item name="active" label="启用" valuePropName="checked">
              <Switch />
            </Form.Item>
          </div>
        </Form>
      </Modal>
    </div>
  );
}
