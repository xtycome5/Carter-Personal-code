import { useState } from 'react';
import { Card, Table, Button, Modal, Form, Input, Select, Tag, Space, Popconfirm, message } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';

interface Artist {
  key: string;
  name: string;
  category: string;
  style: string;
  enabled: boolean;
}

const CATEGORIES = [
  '超现实核心',
  '表现主义/扭曲',
  '诗意失重',
  '神秘象征',
  '现代梦幻',
];

const initialArtists: Artist[] = [
  { key: 'DALI', name: 'Salvador Dalí', category: '超现实核心', style: 'melting forms, warped time-space, impossibly detailed renderings of impossible things', enabled: true },
  { key: 'MAGRITTE', name: 'René Magritte', category: '超现实核心', style: 'calm paradoxes in impossible situations, philosophical mystery, uncanny stillness', enabled: true },
  { key: 'ERNST', name: 'Max Ernst', category: '超现实核心', style: 'collage textures, organic alien forms, jungle-like otherworlds, frottage surfaces', enabled: true },
  { key: 'VARO', name: 'Remedios Varo', category: '超现实核心', style: 'alchemical machinery, spiral architecture, feminine mysticism, mechanical dreamscapes', enabled: true },
  { key: 'CARRINGTON', name: 'Leonora Carrington', category: '超现实核心', style: 'magical creatures, Celtic mythology, alchemical dreamscapes, hybrid beings', enabled: true },
  { key: 'MUNCH', name: 'Edvard Munch', category: '表现主义/扭曲', style: 'emotions distorting reality, expressionist anxiety, undulating forms, raw psychic energy', enabled: true },
  { key: 'SCHIELE', name: 'Egon Schiele', category: '表现主义/扭曲', style: 'twisted bodies, raw emotional linework, exposed vulnerability, angular tension', enabled: true },
  { key: 'BACON', name: 'Francis Bacon', category: '表现主义/扭曲', style: 'distorted flesh, caged screaming forms, violent blurring, visceral smeared humanity', enabled: true },
  { key: 'CHAGALL', name: 'Marc Chagall', category: '诗意失重', style: 'weightless floating, jewel-tone colors, poetic tenderness, lovers drifting above villages', enabled: true },
  { key: 'REDON', name: 'Odilon Redon', category: '诗意失重', style: 'pastel dreamscapes, floating eyeballs, faces emerging from flowers, luminous color fields', enabled: true },
  { key: 'KLIMT', name: 'Gustav Klimt', category: '诗意失重', style: 'gold-leaf patterns, ornamental sensuality, Byzantine opulence, mosaic textures', enabled: true },
  { key: 'MUCHA', name: 'Alphonse Mucha', category: '诗意失重', style: 'flowing hair halos, art nouveau curves, nature-entwined figures, decorative borders', enabled: true },
  { key: 'BOSCH', name: 'Hieronymus Bosch', category: '神秘象征', style: 'teeming hellscapes, bizarre creatures, moral allegory, miniature surreal vignettes', enabled: true },
  { key: 'BLAKE', name: 'William Blake', category: '神秘象征', style: 'prophetic visions, muscular angels, radiant cosmos, hand-tinted engravings', enabled: true },
  { key: 'BEKSINSKI', name: 'Zdzisław Beksiński', category: '神秘象征', style: 'bone cathedrals, post-apocalyptic grandeur, warm-hued nightmares, organic architecture', enabled: true },
  { key: 'KUSAMA', name: 'Yayoi Kusama', category: '现代梦幻', style: 'infinite polka dots, mirrored infinity rooms, pumpkin obsession, cosmic repetition', enabled: true },
  { key: 'DECHIRICO', name: 'Giorgio de Chirico', category: '现代梦幻', style: 'elongated shadows, empty piazzas, metaphysical stillness, anachronistic architecture', enabled: true },
  { key: 'SAGE', name: 'Kay Sage', category: '现代梦幻', style: 'draped architectural forms, barren landscapes, geometric ghost-like structures, muted palette', enabled: true },
];

export default function ArtistPoolPage() {
  const [artists, setArtists] = useState<Artist[]>(initialArtists);
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Artist | null>(null);
  const [form] = Form.useForm();

  const handleAdd = () => {
    setEditing(null);
    form.resetFields();
    setModalOpen(true);
  };

  const handleEdit = (record: Artist) => {
    setEditing(record);
    form.setFieldsValue(record);
    setModalOpen(true);
  };

  const handleDelete = (key: string) => {
    setArtists(artists.filter(a => a.key !== key));
    message.success('Artist removed');
  };

  const handleSave = () => {
    form.validateFields().then(values => {
      if (editing) {
        setArtists(artists.map(a => a.key === editing.key ? { ...a, ...values } : a));
        message.success('Artist updated');
      } else {
        const newKey = values.name.split(' ').pop()?.toUpperCase() || 'NEW';
        setArtists([...artists, { ...values, key: newKey, enabled: true }]);
        message.success('Artist added');
      }
      setModalOpen(false);
    });
  };

  const toggleEnabled = (key: string) => {
    setArtists(artists.map(a => a.key === key ? { ...a, enabled: !a.enabled } : a));
  };

  const columns = [
    {
      title: 'Artist',
      dataIndex: 'name',
      key: 'name',
      render: (name: string, record: Artist) => (
        <span style={{ opacity: record.enabled ? 1 : 0.4 }}>{name}</span>
      ),
    },
    {
      title: 'Category',
      dataIndex: 'category',
      key: 'category',
      filters: CATEGORIES.map(c => ({ text: c, value: c })),
      onFilter: (value: any, record: Artist) => record.category === value,
      render: (v: string) => <Tag>{v}</Tag>,
    },
    {
      title: 'Style Description',
      dataIndex: 'style',
      key: 'style',
      ellipsis: true,
      width: 300,
    },
    {
      title: 'Status',
      dataIndex: 'enabled',
      key: 'enabled',
      render: (enabled: boolean, record: Artist) => (
        <Tag
          color={enabled ? 'green' : 'default'}
          style={{ cursor: 'pointer' }}
          onClick={() => toggleEnabled(record.key)}
        >
          {enabled ? 'Active' : 'Disabled'}
        </Tag>
      ),
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_: any, record: Artist) => (
        <Space>
          <Button size="small" icon={<EditOutlined />} onClick={() => handleEdit(record)} />
          <Popconfirm title="Delete this artist?" onConfirm={() => handleDelete(record.key)}>
            <Button size="small" icon={<DeleteOutlined />} danger />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  const enabledCount = artists.filter(a => a.enabled).length;

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div>
          <h2 style={{ color: '#f0f0f5', margin: 0 }}>画家池管理</h2>
          <p style={{ color: '#9ca3af', fontSize: 13, margin: '4px 0 0' }}>
            {enabledCount} active / {artists.length} total — 每次生图随机取 3 位
          </p>
        </div>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
          添加画家
        </Button>
      </div>

      <Card>
        <Table
          dataSource={artists}
          columns={columns}
          rowKey="key"
          pagination={false}
          size="small"
        />
      </Card>

      <Modal
        title={editing ? '编辑画家' : '添加画家'}
        open={modalOpen}
        onOk={handleSave}
        onCancel={() => setModalOpen(false)}
        okText="Save"
      >
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="Artist Name" rules={[{ required: true }]}>
            <Input placeholder="e.g. Salvador Dalí" />
          </Form.Item>
          <Form.Item name="category" label="Category" rules={[{ required: true }]}>
            <Select options={CATEGORIES.map(c => ({ label: c, value: c }))} />
          </Form.Item>
          <Form.Item name="style" label="Style Description" rules={[{ required: true }]}>
            <Input.TextArea rows={3} placeholder="Visual style keywords for prompt generation..." />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
