import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Table, Tag, Card, Statistic, Row, Col, Button, Modal, Form, Input, message, Progress } from "antd";
import { ipamApi } from "../../api/modules";
import { useState } from "react";

export default function SubnetTreePage() {
  const qc = useQueryClient();
  const [open, setOpen] = useState(false);
  const [form] = Form.useForm();
  const { data, isLoading } = useQuery({ queryKey: ["subnets"], queryFn: () => ipamApi.listSubnets({ page_size: 100 }).then(r => r.data) });
  const { data: allocs } = useQuery({ queryKey: ["allocations"], queryFn: () => ipamApi.listAllocations({ page_size: 100 }).then(r => r.data) });
  const createMu = useMutation({ mutationFn: (v: any) => ipamApi.createSubnet(v), onSuccess: () => { qc.invalidateQueries({ queryKey: ["subnets"] }); setOpen(false); form.resetFields(); } });

  return (
    <div>
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={8}><Card size="small"><Statistic title="子网数" value={data?.total || 0} /></Card></Col>
        <Col span={8}><Card size="small"><Statistic title="IP分配" value={allocs?.total || 0} /></Card></Col>
        <Col span={8}><Card size="small"><Button type="primary" onClick={() => setOpen(true)}>新增子网</Button></Col>
      </Row>
      <Card title="子网列表">
        {(data?.items || []).map((s: any) => (
          <Card key={s.id} size="small" style={{ marginBottom: 12 }}>
            <Row justify="space-between" align="middle">
              <Col span={6}><strong>{s.cidr}</strong><br/>{s.description || "-"}</Col>
              <Col span={6}>网关: {s.gateway || "-"} | VLAN: {s.vlan_id || "-"}</Col>
              <Col span={12}><Progress percent={s.total_ips ? Math.round(s.used_ips / s.total_ips * 100) : 0} size="small" format={() => `${s.used_ips}/${s.total_ips}`} /></Col>
            </Row>
          </Card>
        ))}
      </Card>
      <Card title="IP 分配" style={{ marginTop: 16 }}>
        <Table dataSource={allcs?.items || []} rowKey="id" loading={isLoading} size="small" pagination={false}
          columns={[
            { title: "IP", dataIndex: "ip_address" },
            { title: "状态", dataIndex: "status", render: (s: string) => <Tag color={s==="allocated"?"blue":s==="reserved"?"orange":"default"}>{s}</Tag> },
            { title: "设备", dataIndex: "device_id", render: (d: string) => d || "-" },
            { title: "来源", dataIndex: "source" },
          ]} />
      </Card>
      <Modal title="新增子网" open={open} onCancel={() => setOpen(false)} onOk={() => form.submit()}>
        <Form form={form} layout="vertical" onFinish={v => createMu.mutate(v)}>
          <Form.Item name="cidr" label="CIDR" rules={[{ required: true }]}><Input placeholder="10.1.0.0/16" /></Form.Item>
          <Form.Item name="description" label="描述"><Input /></Form.Item>
          <Form.Item name="gateway" label="网关"><Input /></Form.Item>
          <Form.Item name="vlan_id" label="VLAN ID"><Input type="number" /></Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
