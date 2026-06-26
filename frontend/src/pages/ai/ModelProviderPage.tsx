import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Card, Table, Tag, Button, Modal, Form, Input, Select, Space, message, Descriptions, Popconfirm } from "antd";
import { PlusOutlined, ApiOutlined, LinkOutlined, CheckCircleOutlined } from "@ant-design/icons";
import client from "../../api/client";

export default function ModelProviderPage() {
  const qc = useQueryClient();
  const [open, setOpen] = useState(false);
  const [form] = Form.useForm();

  const { data, isLoading } = useQuery({
    queryKey: ["model-providers"],
    queryFn: () => client.get("/ai/models").then(r => r.data),
  });

  const { data: presets } = useQuery({
    queryKey: ["model-presets"],
    queryFn: () => client.get("/ai/models/presets").then(r => r.data),
  });

  const createMu = useMutation({
    mutationFn: (v: any) => client.post("/ai/models", v),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["model-providers"] }); setOpen(false); form.resetFields(); message.success("Created"); },
  });

  const testMu = useMutation({
    mutationFn: (id: string) => client.post(`/ai/models/${id}/test`),
    onSuccess: (r: any) => { message.info(r.data?.message || "Test completed"); },
  });

  const delMu = useMutation({
    mutationFn: (id: string) => client.post(`/ai/models/${id}/delete`),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["model-providers"] }); message.success("Deleted"); },
  });

  const quickCreate = (preset: any) => {
    form.setFieldsValue({
      name: preset.type,
      provider_type: preset.type,
      base_url: preset.base_url,
      default_model: preset.default_model,
      input_price: preset.input_price,
      output_price: preset.output_price,
    });
    setOpen(true);
  };

  return (
    <div>
      {/* Built-in presets */}
      <Card title="内置模型预设" size="small" style={{ marginBottom: 16 }}>
        <Space wrap>
          {(presets?.presets || []).map((p: any) => (
            <Card key={p.type} size="small" hoverable style={{ width: 220 }}
                  onClick={() => quickCreate(p)}>
              <Space><ApiOutlined /><strong>{p.type}</strong></Space>
              <br /><span style={{ fontSize: 12, color: "#888" }}>{p.base_url}</span>
              <br /><Tag style={{ marginTop: 4 }}>{p.default_model}</Tag>
              <Tag>¥{p.input_price}/{p.output_price}</Tag>
            </Card>
          ))}
        </Space>
      </Card>

      {/* Configured providers */}
      <Card title="已配置的模型" extra={<Button type="primary" icon={<PlusOutlined />} onClick={() => { form.resetFields(); setOpen(true); }}>新增</Button>}>
        <Table dataSource={data?.items || []} rowKey="id" loading={isLoading} pagination={false} size="middle"
          columns={[
            { title: "名称", dataIndex: "name", render: (t: string, r: any) => <Space><ApiOutlined />{t}</Space> },
            { title: "类型", dataIndex: "provider_type", width: 120 },
            { title: "默认模型", dataIndex: "default_model", width: 160 },
            { title: "状态", dataIndex: "is_enabled", width: 70, render: (v: boolean) => <Tag color={v ? "green" : "default"}>{v ? "启用" : "停用"}</Tag> },
            { title: "操作", width: 180, render: (_: any, r: any) => (
              <Space size="small">
                <Button size="small" icon={<CheckCircleOutlined />} onClick={() => testMu.mutate(r.id)} loading={testMu.isPending}>测试</Button>
                <Popconfirm title="确定删除?" onConfirm={() => delMu.mutate(r.id)}>
                  <Button size="small" danger>删除</Button>
                </Popconfirm>
              </Space>
            )},
          ]} />
      </Card>

      {/* Create/Edit modal */}
      <Modal title="新增模型提供商" open={open} onCancel={() => setOpen(false)} onOk={() => form.submit()} confirmLoading={createMu.isPending} width={520}>
        <Form form={form} layout="vertical" onFinish={v => createMu.mutate(v)}>
          <Form.Item name="name" label="名称" rules={[{ required: true }]}><Input placeholder="DeepSeek" /></Form.Item>
          <Form.Item name="provider_type" label="类型" rules={[{ required: true }]}>
            <Select options={(presets?.presets || []).map((p: any) => ({ value: p.type, label: p.type }))} />
          </Form.Item>
          <Form.Item name="base_url" label="API 地址" rules={[{ required: true }]}><Input placeholder="https://api.deepseek.com/v1" /></Form.Item>
          <Form.Item name="api_key_encrypted" label="API Key"><Input.Password placeholder="sk-..." /></Form.Item>
          <Form.Item name="default_model" label="默认模型" rules={[{ required: true }]}><Input placeholder="deepseek-chat" /></Form.Item>
          <Form.Item label="价格 (每百万 tokens)">
            <Input.Group compact>
              <Form.Item name="input_price" noStyle><Input placeholder="输入价格" style={{ width: "48%", marginRight: "4%" }} /></Form.Item>
              <Form.Item name="output_price" noStyle><Input placeholder="输出价格" style={{ width: "48%" }} /></Form.Item>
            </Input.Group>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
