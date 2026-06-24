import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Card, Table, Tag, Typography, Space, Row, Col, Statistic } from "antd";
import { NodeIndexOutlined } from "@ant-design/icons";
import client from "../../api/client";

const { Text } = Typography;
const healthLabel: Record<string, string> = { healthy: "健康", warning: "警告", critical: "异常" };
const healthColor: Record<string, string> = { healthy: "green", warning: "orange", critical: "red" };

export default function ServiceListPage() {
  const navigate = useNavigate();
  const { data, isLoading } = useQuery({ queryKey: ["services"], queryFn: () => client.get("/apm/services").then((r) => r.data) });

  const columns = [
    { title: "服务名称", dataIndex: "display_name", key: "name", render: (t: string, r: any) => <a onClick={() => navigate(`/apm/services/${r.id}`)}>{t}</a> },
    { title: "语言/类型", dataIndex: "language", key: "lang", width: 90 },
    { title: "实例数", dataIndex: "instances", key: "instances", width: 70 },
    { title: "P99 延迟", dataIndex: "p99_latency_ms", key: "latency", width: 100, render: (v: number) => <Text style={{ color: v > 1000 ? "#f5222d" : v > 200 ? "#fa8c16" : "#3f8600" }}>{v}ms</Text> },
    { title: "错误率", dataIndex: "error_rate_pct", key: "error", width: 90, render: (v: number) => <Text style={{ color: v > 1 ? "#f5222d" : "#3f8600" }}>{v}%</Text> },
    { title: "吞吐量", dataIndex: "throughput_rps", key: "rps", width: 80, render: (v: number) => `${v} RPS` },
    { title: "健康状态", dataIndex: "health", key: "health", width: 90, render: (h: string) => <Tag color={healthColor[h]}>{healthLabel[h]}</Tag> },
  ];

  return (
    <div>
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}><Card size="small"><Statistic title="服务总数" value={data?.items?.length || 0} prefix={<NodeIndexOutlined />} /></Card></Col>
        <Col span={6}><Card size="small"><Statistic title="健康" value={data?.items?.filter((s: any) => s.health === "healthy").length || 0} valueStyle={{ color: "#3f8600" }} /></Card></Col>
        <Col span={6}><Card size="small"><Statistic title="警告" value={data?.items?.filter((s: any) => s.health === "warning").length || 0} valueStyle={{ color: "#fa8c16" }} /></Card></Col>
        <Col span={6}><Card size="small"><Statistic title="异常" value={data?.items?.filter((s: any) => s.health === "critical").length || 0} valueStyle={{ color: "#cf1322" }} /></Card></Col>
      </Row>
      <Card title={<Space><NodeIndexOutlined />应用服务列表</Space>} extra={<Text type="secondary">数据来源: SigNoz APM</Text>}>
        <Table columns={columns} dataSource={data?.items || []} rowKey="id" loading={isLoading} size="middle" pagination={false} />
      </Card>
    </div>
  );
}
