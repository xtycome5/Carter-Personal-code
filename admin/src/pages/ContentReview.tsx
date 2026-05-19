import { useEffect, useState } from 'react';
import { Card, Image, Tabs, Spin, Button, Checkbox, message, Tag, Empty, Tooltip } from 'antd';
import { CheckOutlined, CloseOutlined, PictureOutlined, VideoCameraOutlined } from '@ant-design/icons';
import { adminAPI } from '../lib/api';

export default function ContentReviewPage() {
  const [pendingData, setPendingData] = useState<any[]>([]);
  const [featuredData, setFeaturedData] = useState<any[]>([]);
  const [pendingTotal, setPendingTotal] = useState(0);
  const [featuredTotal, setFeaturedTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [activeTab, setActiveTab] = useState('pending');

  const fetchPending = (page = 1) => {
    setLoading(true);
    adminAPI.galleryPending(page)
      .then(res => {
        setPendingData(res.items || []);
        setPendingTotal(res.total || 0);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  const fetchFeatured = (page = 1) => {
    setLoading(true);
    adminAPI.galleryFeatured(page)
      .then(res => {
        setFeaturedData(res.items || []);
        setFeaturedTotal(res.total || 0);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchPending(); fetchFeatured(); }, []);

  const handleApprove = async () => {
    if (selectedIds.length === 0) { message.warning('请选择要上架的作品'); return; }
    try {
      await adminAPI.galleryApprove(selectedIds);
      message.success(`已上架 ${selectedIds.length} 个作品`);
      setSelectedIds([]);
      fetchPending();
      fetchFeatured();
    } catch (e: any) {
      message.error(e.message);
    }
  };

  const handleReject = async (ids: string[]) => {
    try {
      await adminAPI.galleryReject(ids);
      message.success(`已下架 ${ids.length} 个作品`);
      fetchFeatured();
    } catch (e: any) {
      message.error(e.message);
    }
  };

  const toggleSelect = (id: string) => {
    setSelectedIds(prev =>
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    );
  };

  const selectAll = () => {
    if (selectedIds.length === pendingData.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(pendingData.map(i => i.id));
    }
  };

  const renderMediaCard = (item: any, showCheckbox: boolean, showReject: boolean) => (
    <div
      key={item.id}
      style={{
        position: 'relative',
        borderRadius: 12,
        overflow: 'hidden',
        background: '#1a1a2e',
        border: selectedIds.includes(item.id) ? '2px solid #7c5cfc' : '2px solid transparent',
        cursor: showCheckbox ? 'pointer' : 'default',
      }}
      onClick={() => showCheckbox && toggleSelect(item.id)}
    >
      {/* Media */}
      <div style={{ aspectRatio: '1', position: 'relative' }}>
        {item.type === 'image' ? (
          <Image
            src={item.result_url}
            style={{ width: '100%', height: '100%', objectFit: 'cover' }}
            preview={{ mask: '查看大图' }}
            onClick={(e) => e?.stopPropagation()}
          />
        ) : (
          <video
            src={item.result_url}
            style={{ width: '100%', height: '100%', objectFit: 'cover' }}
            muted
            loop
            playsInline
            onMouseOver={(e) => (e.target as HTMLVideoElement).play()}
            onMouseOut={(e) => { const v = e.target as HTMLVideoElement; v.pause(); v.currentTime = 0; }}
          />
        )}
        {/* Type badge */}
        <div style={{ position: 'absolute', top: 8, left: 8 }}>
          <Tag color={item.type === 'image' ? 'purple' : 'blue'} style={{ margin: 0 }}>
            {item.type === 'image' ? <PictureOutlined /> : <VideoCameraOutlined />}
          </Tag>
        </div>
        {/* Checkbox */}
        {showCheckbox && (
          <div style={{ position: 'absolute', top: 8, right: 8 }} onClick={(e) => e.stopPropagation()}>
            <Checkbox checked={selectedIds.includes(item.id)} onChange={() => toggleSelect(item.id)} />
          </div>
        )}
        {/* Reject button for featured */}
        {showReject && (
          <div style={{ position: 'absolute', top: 8, right: 8 }}>
            <Button
              type="primary"
              danger
              size="small"
              icon={<CloseOutlined />}
              onClick={() => handleReject([item.id])}
            >
              下架
            </Button>
          </div>
        )}
      </div>
      {/* Info */}
      <div style={{ padding: '8px 10px' }}>
        <Tooltip title={item.dream_title || item.dream_content}>
          <p style={{ color: '#f0f0f5', fontSize: 13, margin: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {item.dream_title || item.dream_content || '—'}
          </p>
        </Tooltip>
        <p style={{ color: '#6b7280', fontSize: 11, margin: '2px 0 0' }}>{item.user}</p>
      </div>
    </div>
  );

  return (
    <div>
      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2 style={{ color: '#f0f0f5', margin: 0 }}>Gallery 审核</h2>
          <p style={{ color: '#9ca3af', fontSize: 13, margin: '4px 0 0' }}>
            待审核 {pendingTotal} · 已上架 {featuredTotal}
          </p>
        </div>
        {activeTab === 'pending' && (
          <div style={{ display: 'flex', gap: 8 }}>
            <Button onClick={selectAll}>
              {selectedIds.length === pendingData.length && pendingData.length > 0 ? '取消全选' : '全选'}
            </Button>
            <Button
              type="primary"
              icon={<CheckOutlined />}
              onClick={handleApprove}
              disabled={selectedIds.length === 0}
            >
              上架 ({selectedIds.length})
            </Button>
          </div>
        )}
      </div>

      <Card>
        <Tabs
          activeKey={activeTab}
          onChange={(key) => { setActiveTab(key); setSelectedIds([]); }}
          items={[
            { key: 'pending', label: `待审核 (${pendingTotal})` },
            { key: 'featured', label: `已上架 (${featuredTotal})` },
          ]}
        />
        <Spin spinning={loading}>
          {activeTab === 'pending' ? (
            pendingData.length > 0 ? (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 16 }}>
                {pendingData.map(item => renderMediaCard(item, true, false))}
              </div>
            ) : (
              <Empty description="没有待审核的作品" />
            )
          ) : (
            featuredData.length > 0 ? (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 16 }}>
                {featuredData.map(item => renderMediaCard(item, false, true))}
              </div>
            ) : (
              <Empty description="还没有上架的作品" />
            )
          )}
        </Spin>
      </Card>
    </div>
  );
}
