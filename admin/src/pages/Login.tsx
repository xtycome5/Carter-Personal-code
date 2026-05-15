import { useState } from 'react';
import { Card, Form, Input, Button, message } from 'antd';
import { LockOutlined, UserOutlined } from '@ant-design/icons';

export default function LoginPage() {
  const [loading, setLoading] = useState(false);

  const onFinish = (values: { email: string; password: string }) => {
    setLoading(true);
    // TODO: real admin auth
    setTimeout(() => {
      if (values.email === 'admin@dreamrecorder.xyz' && values.password === 'admin123') {
        localStorage.setItem('admin_token', 'mock-admin-token');
        window.location.href = '/dashboard';
      } else {
        message.error('Invalid credentials');
      }
      setLoading(false);
    }, 800);
  };

  return (
    <div style={{
      minHeight: '100vh',
      background: '#0c0c14',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
    }}>
      <Card style={{ width: 400, background: '#1e1e32', border: '1px solid rgba(255,255,255,0.06)' }}>
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <h1 style={{ color: '#7c5cfc', fontSize: 24, fontWeight: 700, margin: 0 }}>
            Dream Recorder
          </h1>
          <p style={{ color: '#6b7280', fontSize: 13, margin: '8px 0 0' }}>Admin Panel</p>
        </div>

        <Form onFinish={onFinish} layout="vertical" size="large">
          <Form.Item name="email" rules={[{ required: true, message: 'Email required' }]}>
            <Input prefix={<UserOutlined />} placeholder="Admin email" />
          </Form.Item>
          <Form.Item name="password" rules={[{ required: true, message: 'Password required' }]}>
            <Input.Password prefix={<LockOutlined />} placeholder="Password" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" block loading={loading}>
              Sign In
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
}
