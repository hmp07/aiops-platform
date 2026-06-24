import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Table, Tag, Space, Card, Typography, Button, Modal, Form, Input, Select, message } from "antd";
import { DesktopOutlined, PlusOutlined } from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import { deviceApi } from "../../api/modules";

const { Text } = Typography;
const statusColor: Record<string, string> = { in_use: "green", spare: "orange", retired: "default" };

export default function DeviceListPage() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [open, setOpen] = useState(false);
  const [form] = Form.useForm();
  const { data, isLoading } = useQuery({ queryKey: ["devices"], queryFn: () => deviceApi.list({ page_size: 100 }).then(r => r.data) });
  const createMu = useMutation({ mutationFn: (v: any) => deviceApi.create(v), onSuccess: () => { qc.invalidateQueries({ queryKey: ["devices"] }); setOpen(false); form.resetFields(); message.success("OK"); } });

  const columns = [
    { title: "名称", dataIndex: "device_name", render: (t: string, r: any) => <a onClick={() => navigate(`/asset/${r.id}`)}>{t}</a> },
    { title: "类型", dataIndex: "device_type", width: 70 },
    { title: "厂商", dataIndex: "vendor", width: 70 },
    { title: "型号", dataIndex: "model", width: 140, ellipsis: true },
    { title: "管理IP", dataIndex: "management_ip", width: 120 },
    { title: "位置", dataIndex: "location", width: 120, ellipsis: true },
    { title: "状态", dataIndex: "lifecycle_status", width: 70, render: (s: string) => <Tag color={statusColor[s]}>{s}</Tag> },
  ];

  return (
    <div>
      <Card title={<Space><DesktopOutlined />设备资产管理</Space>} extra={<Text type="secondary">共 {data?.total || 0} 台</Text>}>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setOpen(true)} style={{ marginBottom: 16 }}>新增设备</Button>
        <Table columns={columns} dataSource={data?.items || []} rowKey="id" loading={isLoading} size="middle" pagination={{ pageSize: 20 }} />
      </Card>
      <Modal title="新增设备" open={open} onCancel={() => setOpen(false)} onOk={() => form.submit()} confirmLoading={createMu.isPending}>
        <Form form={form} layout="vertical" onFinish={v => createMu.mutate(v)}>
          <Form.Item name="device_name" label="名称" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="device_type" label="类型" rules={[{ required: true }]}><Select options={["switch","router","firewall","server"].map(s=>({value:s,label:s}))} /></Form.Item>
          <Form.Item name="vendor" label="厂商" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="model" label="型号" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="management_ip" label="管理IP"><Input /></Form.Item>
          <Form.Item name="location" label="位置"><Input /></Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
