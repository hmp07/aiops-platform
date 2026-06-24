import { useParams, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Descriptions, Tag, Card, Button, Space, Typography, Spin, Empty, Timeline, message } from "antd";
import { ArrowLeftOutlined } from "@ant-design/icons";
import { alertApi } from "../../api/modules";

const { Title, Text } = Typography;
const severityColor: Record<string, string> = { critical: "red", warning: "orange", info: "blue" };
const statusLabel: Record<string, string> = { triggered: "待处理", acknowledged: "已认领", in_progress: "处理中", resolved: "已解决", closed: "已关闭" };

export default function AlertDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { data: alert, isLoading } = useQuery({ queryKey: ["alert", id], queryFn: () => alertApi.get(id!).then(r => r.data), enabled: !!id });

  const handleAck = async () => { await alertApi.acknowledge(id!); message.success("已认领"); navigate(0); };
  const handleResolve = async () => { await alertApi.resolve(id!); message.success("已解决"); navigate(0); };
  const handleClose = async () => { await alertApi.close(id!); message.success("已关闭"); navigate(0); };

  if (isLoading) return <Spin size="large" style={{ display: "block", margin: "200px auto" }} />;
  if (!alert) return <Empty description="未找到告警" />;

  return (
    <div>
      <Button icon={<ArrowLeftOutlined />} onClick={() => navigate("/monitoring/alerts")} style={{ marginBottom: 16 }}>返回告警列表</Button>
      <Card>
        <Descriptions title={<Space><Tag color={severityColor[alert.severity]}>{alert.severity}</Tag>{alert.title}</Space>} bordered column={3} size="small">
          <Descriptions.Item label="状态"><Tag>{statusLabel[alert.status]}</Tag></Descriptions.Item>
          <Descriptions.Item label="来源">{alert.source}</Descriptions.Item>
          <Descriptions.Item label="时间">{new Date(alert.time).toLocaleString()}</Descriptions.Item>
          <Descriptions.Item label="设备ID">{alert.device_id || "-"}</Descriptions.Item>
          <Descriptions.Item label="规则ID">{alert.rule_id || "-"}</Descriptions.Item>
          <Descriptions.Item label="认领人">{alert.acknowledged_by || "-"}</Descriptions.Item>
        </Descriptions>
        {alert.description && <div style={{ marginTop: 12, padding: 12, background: "#fafafa", borderRadius: 8 }}><Text>{alert.description}</Text></div>}
        {alert.root_cause && <Card title="AI 根因分析" size="small" style={{ marginTop: 12 }}><pre>{JSON.stringify(alert.root_cause, null, 2)}</pre></Card>}
        <Space style={{ marginTop: 16 }}>
          {alert.status === "triggered" && <Button type="primary" onClick={handleAck}>认领</Button>}
          {(alert.status === "acknowledged" || alert.status === "in_progress") && <Button type="primary" onClick={handleResolve}>解决</Button>}
          {alert.status === "resolved" && <Button onClick={handleClose}>关闭</Button>}
        </Space>
      </Card>
    </div>
  );
}
