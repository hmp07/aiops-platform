import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Table, Tag, Card, Button, Modal, Form, Input, Select, message } from "antd";
import { apmApi } from "../../api/modules";
import { useState } from "react";

const healthColor: Record<string, string> = { healthy: "green", warning: "orange", critical: "red" };

export default function ServiceListPage() {
  const qc = useQueryClient();
  const [open, setOpen] = useState(false);
  const [form] = Form.useForm();
  const { data, isLoading } = useQuery({ queryKey: ["services"], queryFn: () => apmApi.listServices({ page_size: 100 }).then(r => r.data) });
  const createMu = useMutation({ mutationFn: (v: any) => apmApi.createService(v), onSuccess: () => { qc.invalidateQueries({ queryKey: ["services"] }); setOpen(false); form.resetFields(); } });

  return (
    <div>
      <Card title="应用服务列表" extra={<Button type="primary" onClick={() => setOpen(true)}>新增服务</Button>}>
        <Table columns={[
          { title: "名称", dataIndex: "display_name" },
          { title: "语言", dataIndex: "language", width: 80 },
          { title: "实例", dataIndex: "instances", width: 60 },
          { title: "P99延迟", dataIndex: "p99_latency_ms", width: 90, render: (v: number) => `${v}ms` },
          { title: "错误率", dataIndex: "error_rate_pct", width: 80, render: (v: number) => `${v}%` },
          { title: "吞吐", dataIndex: "throughput_rps", width: 80, render: (v: number) => `${v} RPS` },
          { title: "健康", dataIndex: "health", width: 70, render: (h: string) => <Tag color={healthColor[h]}>{h}</Tag> },
        ]} dataSource={data?.items || []} rowKey="id" loading={isLoading} size="middle" pagination={false} />
      </Card>
      <Modal title="新增服务" open={open} onCancel={() => setOpen(false)} onOk={() => form.submit()}>
        <Form form={form} layout="vertical" onFinish={v => createMu.mutate(v)}>
          <Form.Item name="name" label="服务名" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="display_name" label="显示名" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="language" label="语言"><Select options={["Java","Go","Python","Node"].map(s=>({value:s,label:s}))} /></Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
