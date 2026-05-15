import { useEffect, useState } from 'react';
import { Card, Row, Col, Statistic, Table, Tag, Select, Spin } from 'antd';
import { ThunderboltOutlined, ClockCircleOutlined, ApiOutlined, WarningOutlined } from '@ant-design/icons';
import { adminAPI } from '../lib/api';

interface ApiCall {
  id: string;
  model: string;
  endpoint: string;
  duration_ms: number;
  status: string;
  tokens_input: number;
  tokens_output: number;
  error?: string;
  created_at: string;
}

interface ModelStat {
  model: string;
  calls: number;
  avg_latency_ms: number;
  successes: number;
  failures: number;
  error_rate: number;
  tokens_in: number;
  tokens_out: number;
}

interface ApiStats {
  period_hours: number;
  total_calls: number;
  success_calls: number;
  failed_calls: number;
  error_rate: number;
  avg_latency_ms: number;
  rpm: number;
  tpm: number;
  total_tokens_in: number;
  total_tokens_out: number;
  model_breakdown: ModelStat[];
  endpoint_breakdown: { endpoint: string; calls: number; avg_latency_ms: number; failures: number }[];
}

export default function ModelMonitorPage() {
  const [stats, setStats] = useState<ApiStats | null>(null);
  const [calls, setCalls] = useState<ApiCall[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [modelFilter, setModelFilter] = useState<string>('all');
  const [hours, setHours] = useState(24);
  const [page, setPage] = useState(1);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [statsRes, callsRes] = await Promise.all([
        adminAPI.getApiStats(hours),
        adminAPI.getApiCalls({
          page,
          hours,
          model: modelFilter === 'all' ? undefined : modelFilter,
        }),
      ]);
      setStats(statsRes);
      setCalls(callsRes.calls || []);
      setTotal(callsRes.total || 0);
    } catch (e) {
      console.error('Failed to fetch API monitoring data:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, [modelFilter, hours, page]);

  const columns = [
    {
      title: 'Model',
      dataIndex: 'model',
      key: 'model',
      render: (v: string) => {
        const color = v.includes('qwen') ? 'purple' : v.includes('happyhorse') ? 'blue' : v.includes('wan') ? 'cyan' : 'default';
        return <Tag color={color}>{v}</Tag>;
      },
    },
    {
      title: 'Endpoint',
      dataIndex: 'endpoint',
      key: 'endpoint',
      render: (v: string) => <code style={{ fontSize: 11, color: '#9ca3af' }}>{v}</code>,
    },
    {
      title: 'Latency',
      dataIndex: 'duration_ms',
      key: 'duration_ms',
      render: (v: number) => v > 0 ? (
        <span style={{ color: v > 5000 ? '#ef4444' : v > 3000 ? '#f59e0b' : '#10b981' }}>
          {v >= 1000 ? `${(v / 1000).toFixed(1)}s` : `${v}ms`}
        </span>
      ) : '—',
      sorter: (a: ApiCall, b: ApiCall) => a.duration_ms - b.duration_ms,
    },
    {
      title: 'Tokens (In/Out)',
      key: 'tokens',
      render: (_: any, record: ApiCall) => record.tokens_input > 0 ? (
        <span style={{ fontSize: 12, color: '#9ca3af' }}>
          {record.tokens_input} / {record.tokens_output}
        </span>
      ) : '—',
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (v: string) => (
        <Tag color={v === 'success' ? 'green' : v === 'timeout' ? 'orange' : 'red'}>{v}</Tag>
      ),
    },
    {
      title: 'Error',
      dataIndex: 'error',
      key: 'error',
      render: (v?: string) => v ? <Tag color="red">{v.slice(0, 40)}</Tag> : '—',
    },
    {
      title: 'Time',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 170,
      render: (v: string) => v ? new Date(v).toLocaleString() : '-',
    },
  ];

  const modelBreakdownColumns = [
    { title: 'Model', dataIndex: 'model', key: 'model', render: (v: string) => <Tag color={v.includes('qwen') ? 'purple' : v.includes('happyhorse') ? 'blue' : 'cyan'}>{v}</Tag> },
    { title: 'Calls', dataIndex: 'calls', key: 'calls' },
    { title: 'Avg Latency', dataIndex: 'avg_latency_ms', key: 'avg_latency_ms', render: (v: number) => v >= 1000 ? `${(v/1000).toFixed(1)}s` : `${v}ms` },
    { title: 'Success', dataIndex: 'successes', key: 'successes', render: (v: number) => <span style={{ color: '#10b981' }}>{v}</span> },
    { title: 'Failed', dataIndex: 'failures', key: 'failures', render: (v: number) => <span style={{ color: v > 0 ? '#ef4444' : '#9ca3af' }}>{v}</span> },
    { title: 'Error Rate', dataIndex: 'error_rate', key: 'error_rate', render: (v: number) => <span style={{ color: v > 0 ? '#ef4444' : '#10b981' }}>{v}%</span> },
    { title: 'Tokens (In/Out)', key: 'tokens', render: (_: any, r: ModelStat) => r.tokens_in > 0 ? `${r.tokens_in} / ${r.tokens_out}` : '—' },
  ];

  const models = stats?.model_breakdown?.map(m => m.model) || [];

  if (loading && !stats) return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div>
          <h2 style={{ color: '#f0f0f5', margin: 0 }}>模型调用监控</h2>
          <p style={{ color: '#9ca3af', fontSize: 13, margin: '4px 0 0' }}>
            DashScope API 实时调用数据 — 最近 {hours} 小时
          </p>
        </div>
        <div style={{ display: 'flex', gap: 12 }}>
          <Select
            value={hours}
            onChange={(v) => { setHours(v); setPage(1); }}
            style={{ width: 120 }}
            options={[
              { label: '最近 1h', value: 1 },
              { label: '最近 6h', value: 6 },
              { label: '最近 24h', value: 24 },
              { label: '最近 3天', value: 72 },
              { label: '最近 7天', value: 168 },
            ]}
          />
          <Select
            value={modelFilter}
            onChange={(v) => { setModelFilter(v); setPage(1); }}
            style={{ width: 200 }}
            options={[
              { label: 'All Models', value: 'all' },
              ...models.map(m => ({ label: m, value: m })),
            ]}
          />
        </div>
      </div>

      {/* Summary Stats */}
      <Row gutter={[16, 16]}>
        <Col span={6}>
          <Card>
            <Statistic
              title="Total Calls"
              value={stats?.total_calls || 0}
              prefix={<ApiOutlined />}
              valueStyle={{ color: '#7c5cfc' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="RPM (Avg)"
              value={stats?.rpm || 0}
              prefix={<ThunderboltOutlined />}
              valueStyle={{ color: '#3b82f6' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Avg Latency"
              value={stats?.avg_latency_ms ? (stats.avg_latency_ms >= 1000 ? (stats.avg_latency_ms / 1000).toFixed(1) : stats.avg_latency_ms) : 0}
              suffix={stats?.avg_latency_ms && stats.avg_latency_ms >= 1000 ? 's' : 'ms'}
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: (stats?.avg_latency_ms || 0) > 5000 ? '#ef4444' : '#10b981' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Error Rate"
              value={stats?.error_rate || 0}
              suffix="%"
              prefix={<WarningOutlined />}
              valueStyle={{ color: (stats?.error_rate || 0) > 0 ? '#ef4444' : '#10b981' }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col span={8}>
          <Card>
            <Statistic title="TPM (Avg)" value={stats?.tpm || 0} prefix={<ThunderboltOutlined />} />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic title="Total Tokens (Input)" value={stats?.total_tokens_in || 0} />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic title="Total Tokens (Output)" value={stats?.total_tokens_out || 0} />
          </Card>
        </Col>
      </Row>

      {/* Model Breakdown */}
      {stats?.model_breakdown && stats.model_breakdown.length > 0 && (
        <Card title="模型维度统计" style={{ marginTop: 24 }}>
          <Table
            dataSource={stats.model_breakdown}
            columns={modelBreakdownColumns}
            rowKey="model"
            pagination={false}
            size="small"
          />
        </Card>
      )}

      {/* Call Log */}
      <Card title="API 调用日志" style={{ marginTop: 24 }}>
        <Table
          dataSource={calls}
          columns={columns}
          rowKey="id"
          loading={loading}
          pagination={{
            current: page,
            pageSize: 50,
            total,
            onChange: (p) => setPage(p),
            showTotal: (t) => `共 ${t} 条`,
          }}
          size="small"
        />
      </Card>
    </div>
  );
}
