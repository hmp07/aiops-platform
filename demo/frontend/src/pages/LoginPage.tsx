import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Form, Input, Button, Card, message, Typography, Space } from "antd";
import { UserOutlined, LockOutlined, DesktopOutlined } from "@ant-design/icons";
import client from "../api/client";
import { useAuthStore } from "../stores/useAuthStore";

const { Title, Text } = Typography;

export default function LoginPage() {
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { login } = useAuthStore();

  const handleSubmit = async (values: { username: string; password: string }) => {
    setLoading(true);
    try {
      const { data } = await client.post("/auth/login", values);
      login(data.access_token, data.user);
      message.success(`欢迎回来，${data.user.display_name}！`);
      navigate("/dashboard");
    } catch {
      message.error("用户名或密码错误，请尝试 admin/admin123");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: "100vh", display: "flex", justifyContent: "center", alignItems: "center", background: "linear-gradient(135deg, #0f2027 0%, #203a43 40%, #2c5364 100%)" }}>
      <Card style={{ width: 420, boxShadow: "0 20px 60px rgba(0,0,0,0.3)", borderRadius: 12 }}>
        <div style={{ textAlign: "center", marginBottom: 32 }}>
          <DesktopOutlined style={{ fontSize: 48, color: "#1677ff", marginBottom: 16 }} />
          <Title level={2} style={{ margin: 0 }}>AIOps Platform</Title>
          <Text type="secondary">AI 智能运维管理平台 Demo</Text>
        </div>
        <Form onFinish={handleSubmit} size="large" initialValues={{ username: "admin", password: "admin123" }}>
          <Form.Item name="username" rules={[{ required: true, message: "请输入用户名" }]}>
            <Input prefix={<UserOutlined />} placeholder="用户名" />
          </Form.Item>
          <Form.Item name="password" rules={[{ required: true, message: "请输入密码" }]}>
            <Input.Password prefix={<LockOutlined />} placeholder="密码" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} block>登 录</Button>
          </Form.Item>
        </Form>
        <Space direction="vertical" style={{ width: "100%", marginTop: 8 }}>
          <Text type="secondary" style={{ fontSize: 12 }}>演示账号：</Text>
          <Text code style={{ fontSize: 11 }}>admin / admin123（管理员）&nbsp;&nbsp;|&nbsp;&nbsp;engineer / engineer123（运维工程师）&nbsp;&nbsp;|&nbsp;&nbsp;viewer / viewer123（只读）</Text>
        </Space>
      </Card>
    </div>
  );
}
