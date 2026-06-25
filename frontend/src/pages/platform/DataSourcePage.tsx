import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Card, Table, Tag, Button, Modal, Form, Input, Select, Space, message, Row, Col, Typography, Switch, Descriptions } from "antd";
import { PlusOutlined, ReloadOutlined, LinkOutlined, ApiOutlined, CloudServerOutlined, NodeIndexOutlined, DatabaseOutlined } from "@ant-design/icons";
import client from "../../api/client";

const { Text, Title } = Typography;

const typeIcons: Record<string, React.ReactNode> = { zabbix: <CloudServerOutlined />, prometheus: <ApiOutlined />, itop: <DatabaseOutlined />, signoz: <NodeIndexOutlined /> };
const statusColor: Record<string, string> = { connected: "green", disconnected: "default", error: "red" };

export default function DataSourcePage() {
  const qc = useQueryClient();
  const [open, setOpen] = useState(false);
  const [editItem, setEditItem] = useState<any>(null);
  const [form] = Form.useForm();
  const { data, isLoading } = useQuery({ queryKey: ["datasources"], queryFn: () => client.get("/datasources").then(r => r.data) });
  const { data: types } = useQuery({ queryKey: ["ds-types"], queryFn: () => client.get("/datasources/types").then(r => r.data) });

  const crMu = useMutation({
    mutationFn: (v: any) => editItem ? client.post(`/datasources/${editItem.id}/update`, v) : client.post("/datasources", v),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["datasources"] }); setOpen(false); form.resetFields(); setEditItem(null); message.success("OK"); }
  });
  const delMu = useMutation({
    mutationFn: (id: string) => client.post(`/datasources/${id}/delete`),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["datasources"] }); message.success("Deleted"); }
  });
  const testMu = useMutation({
    mutationFn: (id: string) => client.post(`/datasources/${id}/test`),
    onSuccess: (r: any) => { message.info(`Status: ${r.data.status}`); qc.invalidateQueries({ queryKey: ["datasources"] }); }
  });
  const syncMu = useMutation({
    mutationFn: (id: string) => client.post(`/datasources/${id}/sync`),
    onSuccess: () => { message.success("Sync completed"); qc.invalidateQueries({ queryKey: ["datasources"] }); }
  });

  const openEdit = (item: any) => { setEditItem(item); form.setFieldsValue(item); setOpen(true); };
  const openNew = () => { setEditItem(null); form.resetFields(); setOpen(true); };

  return (
    <div>
      <Row gutter={16}>
        <Col xs={24} md={8}>
          <Card title="支持的数据源类型" size="small">
            {(types?.items || []).map((t: any) => (
              <Card key={t.type} size="small" style={{ marginBottom: 8 }}>
                <Space>{typeIcons[t.type] || <LinkOutlined />}<Text strong>{t.name}</Text></Space>
                <br /><Text type="secondary" style={{ fontSize: 12 }}>{t.description}</Text>
              </Card>
            ))}
          </Card>
        </Col>
        <Col xs={24} md={16}>
          <Card title="已配置的数据源" extra={<Button type="primary" icon={<PlusOutlined />} onClick={openNew}>新增数据源</Button>}>
            <Table dataSource={data?.items || []} rowKey="id" loading={isLoading} size="middle" pagination={false}
              columns={[
                { title: "名称", dataIndex: "name", render: (t: string, r: any) => <Space>{typeIcons[r.source_type]}{t}</Space> },
                { title: "类型", dataIndex: "source_type", width: 100 },
                { title: "地址", dataIndex: "endpoint_url", width: 200, ellipsis: true },
                { title: "状态", dataIndex: "status", width: 90, render: (s: string) => <Tag color={statusColor[s]}>{s}</Tag> },
                { title: "最后同步", dataIndex: "last_sync_at", width: 150, render: (t: string) => t ? new Date(t).toLocaleString() : "-" },
                { title: "操作", width: 240, render: (_: any, r: any) => (
                  <Space size="small">
                    <Button size="small" onClick={() => testMu.mutate(r.id)} loading={testMu.isPending}>测试</Button>
                    <Button size="small" onClick={() => syncMu.mutate(r.id)} loading={syncMu.isPending}>同步</Button>
                    <Button size="small" onClick={() => openEdit(r)}>编辑</Button>
                    <Button size="small" danger onClick={() => delMu.mutate(r.id)}>删除</Button>
                  </Space>
                )},
              ]} />
          </Card>
        </Col>
      </Row>

      <Modal title={editItem ? "编辑数据源" : "新增数据源"} open={open} onCancel={() => { setOpen(false); setEditItem(null); }} onOk={() => form.submit()} width={560} confirmLoading={crMu.isPending}>
        <Form form={form} layout="vertical" onFinish={v => crMu.mutate(v)}>
          <Form.Item name="name" label="名称" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="source_type" label="类型" rules={[{ required: true }]}>
            <Select options={(types?.items || []).map((t: any) => ({ value: t.type, label: t.name }))} />
          </Form.Item>
          <Form.Item name="endpoint_url" label="API 地址" rules={[{ required: true }]}><Input placeholder="http://zabbix.example.com/api_jsonrpc.php" /></Form.Item>
          <Form.Item name="description" label="描述"><Input /></Form.Item>
          <Form.Item label="认证信息">
            <Form.Item name={["auth_config", "username"]} style={{ display: "inline-block", width: "48%", marginRight: "4%" }}><Input placeholder="用户名" /></Form.Item>
            <Form.Item name={["auth_config", "password"]} style={{ display: "inline-block", width: "48%" }}><Input.Password placeholder="密码" /></Form.Item>
            <Form.Item name={["auth_config", "api_key"]}><Input placeholder="API Key / Token (可选)" /></Form.Item>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
