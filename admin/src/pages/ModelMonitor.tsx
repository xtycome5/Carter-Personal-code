import { useState } from 'react';
import { Card, Row, Col, Statistic, Table, Tag, Select } from 'antd';
import { ThunderboltOutlined, ClockCircleOutlined, ApiOutlined, WarningOutlined } from '@ant-design/icons';

interface ApiCall {
  id: string;
  model: string;
  endpoint: string;
  duration_ms: number;
  status: 'success' | 'failed' | 'timeout';
  tokens_input: number;
  tokens_output: number;
  timestamp: string;
  error?: string;
}

const mockCalls: ApiCall[] = [
  { id: '1', model: 'qwen-plus', endpoint: 'creative_director', duration_ms: 2340, status: 'success', tokens_input: 1250, tokens_output: 680, timestamp: '2026-05-15 16:47:12' },
  { id: '2', model: 'qwen-plus', endpoint: 'prompt_expansion', duration_ms: 3120, status: 'success', tokens_input: 2100, tokens_output: 450, timestamp: '2026-05-15 16:47:15' },
  { id: '3', model: 'happyhorse-1.0-r2v', endpoint: 'video_generation', duration_ms: 145000, status: 'success', tokens_input: 0, tokens_output: 0, timestamp: '2026-05-15 16:47:18' },
  { id: '4', model: 'wan2.1-t2i-turbo', endpoint: 'image_generation', duration_ms: 32000, status: 'success', tokens_input: 0, tokens_output: 0, timestamp: '2026-05-15 16:46:05' },
  { id: '5', model: 'happyhorse-1.0-r2v', endpoint: 'video_generation', duration_ms: 0, status: 'failed', tokens_input: 0, tokens_output: 0, timestamp: '2026-05-15 16:26:00', error: 'DataInspectionFailed' },
  { id: '6', model: 'qwen-plus', endpoint: 'creative_director', duration_ms: 1890, status: 'success', tokens_input: 1180, tokens_output: 720, timestamp: '2026-05-15 16:25:50' },
  { id: '7', model: 'qwen-plus', endpoint: 'prompt_expansion', duration_ms: 2560, status: 'success', tokens_input: 1950, tokens_output: 520, timestamp: '2026-05-15 16:25:53' },
  { id: '8', model: 'happyhorse-1.0-r2v', endpoint: 'video_generation', duration_ms: 0, status: 'failed', tokens_input: 0, tokens_output: 0, timestamp: '2026-05-15 15:50:00', error: 'IPInfringementSuspect' },
  { id: '9', model: 'wan2.1-t2i-turbo', endpoint: 'image_generation', duration_ms: 28500, status: 'success', tokens_input: 0, tokens_output: 0, timestamp: '2026-05-15 15:48:00' },
  { id: '10', model: 'qwen-plus', endpoint: 'creative_director', duration_ms: 5200, status: 'timeout', tokens_input: 1300, tokens_output: 0, timestamp: '2026-05-15 14:30:00', error: 'Request timeout' },
];

export default function ModelMonitorPage() {
  const [modelFilter, setModelFilter] = useState<string>('all');

  const filtered = modelFilter === 'all' ? mockCalls : mockCalls.filter(c => c.model === modelFilter);

  // Compute stats
  const successCalls = filtered.filter(c => c.status === 'success');
  const failedCalls = filtered.filter(c => c.status !== 'success');
  const avgLatency = successCalls.length > 0
    ? Math.round(successCalls.reduce((s, c) => s + c.duration_ms, 0) / successCalls.length)
    : 0;
  const totalTokensIn = filtered.reduce((s, c) => s + c.tokens_input, 0);
  const totalTokensOut = filtered.reduce((s, c) => s + c.tokens_output, 0);

  // Calls per minute (assume last 10 min window for demo)
  const rpm = Math.round(filtered.length / 10 * 60);
  // Tokens per minute
  const tpm = Math.round((totalTokensIn + totalTokensOut) / 10);

  const columns = [
    {
      title: 'Model',
      dataIndex: 'model',
      key: 'model',
      render: (v: string) => {
        const color = v.includes('qwen') ? 'purple' : v.includes('happyhorse') ? 'blue' : 'cyan';
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
      render: (v?: string) => v ? <Tag color="red">{v}</Tag> : '—',
    },
    { title: 'Time', dataIndex: 'timestamp', key: 'timestamp', width: 160 },
  ];

  const models = [...new Set(mockCalls.map(c => c.model))];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div>
          <h2 style={{ color: '#f0f0f5', margin: 0 }}>模型调用监控</h2>
          <p style={{ color: '#9ca3af', fontSize: 13, margin: '4px 0 0' }}>
            DashScope API call metrics — TPM, RPM, latency, errors
          </p>
        </div>
        <Select
          value={modelFilter}
          onChange={setModelFilter}
          style={{ width: 200 }}
          options={[
            { label: 'All Models', value: 'all' },
            ...models.map(m => ({ label: m, value: m })),
          ]}
        />
      </div>

      <Row gutter={[16, 16]}>
        <Col span={6}>
          <Card>
            <Statistic
              title="RPM (Requests/Min)"
              value={rpm}
              prefix={<ApiOutlined />}
              valueStyle={{ color: '#7c5cfc' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="TPM (Tokens/Min)"
              value={tpm}
              prefix={<ThunderboltOutlined />}
              valueStyle={{ color: '#3b82f6' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Avg Latency"
              value={avgLatency >= 1000 ? (avgLatency / 1000).toFixed(1) : avgLatency}
              suffix={avgLatency >= 1000 ? 's' : 'ms'}
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: avgLatency > 5000 ? '#ef4444' : '#10b981' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Error Rate"
              value={filtered.length > 0 ? ((failedCalls.length / filtered.length) * 100).toFixed(1) : 0}
              suffix="%"
              prefix={<WarningOutlined />}
              valueStyle={{ color: failedCalls.length > 0 ? '#ef4444' : '#10b981' }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col span={12}>
          <Card>
            <Statistic title="Total Tokens (Input)" value={totalTokensIn} />
          </Card>
        </Col>
        <Col span={12}>
          <Card>
            <Statistic title="Total Tokens (Output)" value={totalTokensOut} />
          </Card>
        </Col>
      </Row>

      <Card title="API Call Log" style={{ marginTop: 24 }}>
        <Table
          dataSource={filtered}
          columns={columns}
          rowKey="id"
          pagination={{ pageSize: 20 }}
          size="small"
        />
      </Card>
    </div>
  );
}
