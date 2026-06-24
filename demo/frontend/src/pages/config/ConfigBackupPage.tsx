import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Card, Table, Tag, Button, Space, Typography, Spin, Modal, Row, Col, Statistic, Alert } from "antd";
import { CloudServerOutlined, DiffOutlined } from "@ant-design/icons";
import MonacoEditor from "@monaco-editor/react";
import client from "../../api/client";

const { Text, Title } = Typography;

export default function ConfigBackupPage() {
  const [diffVisible, setDiffVisible] = useState(false);
  const { data, isLoading } = useQuery({ queryKey: ["backups"], queryFn: () => client.get("/configs/backups?page_size=50").then((r) => r.data) });
  const { data: stats } = useQuery({ queryKey: ["config-stats"], queryFn: () => client.get("/configs/stats").then((r) => r.data) });
  const { data: diff } = useQuery({ queryKey: ["config-diff"], queryFn: () => client.get("/configs/diff/d1").then((r) => r.data) });

  const columns = [
    { title: "设备", dataIndex: "device_name", key: "device" },
    { title: "备份类型", dataIndex: "backup_type", key: "type", render: (t: string) => t === "scheduled" ? "定时备份" : "手动备份" },
    { title: "状态", dataIndex: "status", key: "status", render: (s: string) => <Tag color={s === "success" ? "green" : "red"}>{s}</Tag> },
    { title: "文件大小", dataIndex: "file_size", key: "size", render: (s: number) => s ? `${(s / 1024).toFixed(1)} KB` : "-" },
    { title: "备份时间", dataIndex: "backup_at", key: "time", render: (t: string) => new Date(t).toLocaleString("zh-CN") },
    { title: "操作", key: "actions", render: (_: any, r: any) => r.device_id === "d1" ? <Button type="link" size="small" icon={<DiffOutlined />} onClick={() => setDiffVisible(true)}>查看 Diff</Button> : null },
  ];

  return (
    <div>
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={8}><Card size="small"><Statistic title="备份总数" value={stats?.total_backups || 0} /></Card></Col>
        <Col span={8}><Card size="small"><Statistic title="成功率" value={stats?.success_rate || 0} suffix="%" valueStyle={{ color: (stats?.success_rate || 0) >= 90 ? "#3f8600" : "#cf1322" }} /></Card></Col>
        <Col span={8}><Card size="small"><Statistic title="失败次数" value={stats?.failed_count || 0} valueStyle={{ color: "#cf1322" }} /></Card></Col>
      </Row>

      <Card title={<Space><CloudServerOutlined />配置备份管理</Space>} extra={<Text type="secondary">变更对比由 AI 进行风险评级 (H8.3)</Text>}>
        <Table columns={columns} dataSource={data?.items || []} rowKey="id" loading={isLoading} size="middle" pagination={{ pageSize: 20 }} />
      </Card>

      <Modal title="配置变更对比 (CORE-SW-01)" open={diffVisible} onCancel={() => setDiffVisible(false)} width={1000} footer={null}>
        {diff ? (
          <>
            <Alert type="error" message={`AI 风险评级: ${diff.risk_analysis?.risk_level === "high" ? "🔴 高危" : "🟢 正常"}`} description={diff.risk_analysis?.reasons?.map((r: string, i: number) => <div key={i}>• {r}</div>)} style={{ marginBottom: 12 }} />
            <div style={{ height: 420 }}>
              <MonacoEditor language="text" theme="vs-dark" options={{ readOnly: true }} value={diff.old_content + '\n\n/* ======================== NEW VERSION ======================== */\n\n' + diff.new_content} />
            </div>
          </>
        ) : <Spin />}
      </Modal>
    </div>
  );
}
