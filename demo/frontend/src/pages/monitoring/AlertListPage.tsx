import { useQuery } from "@tanstack/react-query";
import { Table, Tag, Select, Space, Card, Statistic, Row, Col, Typography } from "antd";
import { AlertOutlined, WarningOutlined, InfoCircleOutlined } from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import client from "../../api/client";

const { Text } = Typography;

const severityColor: Record<string, string> = { critical: "red", warning: "orange", info: "blue" };
const severityIcon: Record<string, React.ReactNode> = { critical: <AlertOutlined />, warning: <WarningOutlined />, info: <InfoCircleOutlined /> };
const statusLabel: Record<string, string> = { triggered: "待处理", acknowledged: "已认领", in_progress: "处理中", resolved: "已解决", closed: "已关闭", suppressed: "已压制" };
const statusColor: Record<string, string> = { triggered: "red", acknowledged: "blue", in_progress: "processing", resolved: "green", closed: "default", suppressed: "default" };

export default function AlertListPage() {
  const navigate = useNavigate();
  const { data, isLoading } = useQuery({ queryKey: ["alerts"], queryFn: () => client.get("/alerts?page_size=50").then((r) => r.data) });
  const { data: stats } = useQuery({ queryKey: ["alert-stats"], queryFn: () => client.get("/alerts/stats").then((r) => r.data) });

  const columns = [
    { title: "告警标题", dataIndex: "title", key: "title", ellipsis: true, render: (t: string, r: any) => <a onClick={() => navigate(`/monitoring/alerts/${r.id}`)}>{t}</a> },
    { title: "严重级别", dataIndex: "severity", key: "severity", width: 100, render: (s: string) => <Tag icon={severityIcon[s]} color={severityColor[s]}>{s === "critical" ? "严重" : s === "warning" ? "警告" : "提示"}</Tag> },
    { title: "状态", dataIndex: "status", key: "status", width: 80, render: (s: string) => <Tag color={statusColor[s]}>{statusLabel[s]}</Tag> },
    { title: "来源", dataIndex: "source", key: "source", width: 80 },
    { title: "设备", dataIndex: "device_name", key: "device", width: 140, ellipsis: true },
    { title: "时间", dataIndex: "time", key: "time", width: 170, render: (t: string) => new Date(t).toLocaleString("zh-CN") },
  ];

  return (
    <div>
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col xs={8} sm={4}><Card size="small"><Statistic title="总计" value={stats?.total || 0} /></Card></Col>
        <Col xs={8} sm={4}><Card size="small"><Statistic title="严重" value={stats?.by_severity?.critical || 0} valueStyle={{ color: "#cf1322" }} prefix={<AlertOutlined />} /></Card></Col>
        <Col xs={8} sm={4}><Card size="small"><Statistic title="警告" value={stats?.by_severity?.warning || 0} valueStyle={{ color: "#fa8c16" }} prefix={<WarningOutlined />} /></Card></Col>
        <Col xs={8} sm={4}><Card size="small"><Statistic title="待处理" value={stats?.by_status?.triggered || 0} valueStyle={{ color: "#cf1322" }} /></Card></Col>
        <Col xs={8} sm={4}><Card size="small"><Statistic title="已解决" value={stats?.by_status?.resolved || 0} valueStyle={{ color: "#3f8600" }} /></Card></Col>
        <Col xs={8} sm={4}><Card size="small"><Statistic title="AI 压制" value={stats?.suppressed_count || 0} valueStyle={{ color: "#8c8c8c" }} prefix={<InfoCircleOutlined />} /></Card></Col>
      </Row>
      <Card title="告警列表" extra={<Text type="secondary">AI 降噪已压制 {stats?.suppressed_count || 0} 条瞬时抖动告警</Text>}>
        <Table columns={columns} dataSource={data?.items || []} rowKey="id" loading={isLoading} size="middle" pagination={{ pageSize: 20, showTotal: (t) => `共 ${t} 条告警` }} />
      </Card>
    </div>
  );
}
