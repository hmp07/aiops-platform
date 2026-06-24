import { useQuery } from "@tanstack/react-query";
import { Row, Col, Card, Statistic, Table, Tag, Typography } from "antd";
import { DesktopOutlined, AlertOutlined, NodeIndexOutlined, CheckCircleOutlined, RobotOutlined, BookOutlined } from "@ant-design/icons";
import ReactEChartsCore from "echarts-for-react";
import { useNavigate } from "react-router-dom";
import client from "../api/client";

const { Text } = Typography;
const severityColor: Record<string, string> = { critical: "red", warning: "orange", info: "blue" };
const statusLabel: Record<string, string> = { triggered: "待处理", acknowledged: "已认领", in_progress: "处理中", resolved: "已解决", closed: "已关闭" };

export default function DashboardPage() {
  const navigate = useNavigate();
  const { data: alerts } = useQuery({ queryKey: ["alerts"], queryFn: () => client.get("/alerts?page_size=100").then(r => r.data) });
  const { data: devices } = useQuery({ queryKey: ["devices"], queryFn: () => client.get("/devices?page_size=5").then(r => r.data) });
  const { data: stats } = useQuery({ queryKey: ["alert-stats"], queryFn: () => client.get("/alerts/stats").then(r => r.data) });
  const { data: services } = useQuery({ queryKey: ["services"], queryFn: () => client.get("/apm/services").then(r => r.data) });

  const alertColumns = [
    { title: "标题", dataIndex: "title", key: "title", ellipsis: true, render: (t: string, r: any) => <a onClick={() => navigate(`/monitoring/alerts/${r.id}`)}>{t}</a> },
    { title: "级别", dataIndex: "severity", key: "severity", width: 70, render: (s: string) => <Tag color={severityColor[s]}>{s}</Tag> },
    { title: "状态", dataIndex: "status", key: "status", width: 70, render: (s: string) => statusLabel[s] || s },
    { title: "来源", dataIndex: "source", key: "source", width: 60 },
  ];

  const trendOption = {
    tooltip: { trigger: "axis" },
    legend: { bottom: 0 },
    grid: { left: 40, right: 20, top: 20, bottom: 40 },
    xAxis: { type: "category", data: ["06-19", "06-20", "06-21", "06-22", "06-23", "06-24", "06-25"] },
    yAxis: { type: "value" },
    series: [
      { name: "严重", type: "line", data: [2, 1, 3, 2, 1, 2, stats?.by_severity?.critical || 0], smooth: true, itemStyle: { color: "#f5222d" } },
      { name: "警告", type: "line", data: [5, 7, 8, 6, 4, 5, stats?.by_severity?.warning || 0], smooth: true, itemStyle: { color: "#fa8c16" } },
      { name: "提示", type: "line", data: [10, 12, 15, 11, 8, 9, stats?.by_severity?.info || 0], smooth: true, itemStyle: { color: "#1890ff" } },
    ],
  };

  return (
    <div>
      <Row gutter={[16, 16]}>
        <Col xs={12} sm={6}><Card hoverable onClick={() => navigate("/asset")}><Statistic title="设备总数" value={devices?.total || 0} prefix={<DesktopOutlined />} /></Card></Col>
        <Col xs={12} sm={6}><Card hoverable onClick={() => navigate("/monitoring/alerts")}><Statistic title="活跃告警" value={stats?.by_status?.triggered || 0} prefix={<AlertOutlined />} valueStyle={{ color: "#cf1322" }} /></Card></Col>
        <Col xs={12} sm={6}><Card hoverable onClick={() => navigate("/apm/services")}><Statistic title="应用服务" value={services?.total || 0} prefix={<NodeIndexOutlined />} /></Card></Col>
        <Col xs={12} sm={6}><Card hoverable onClick={() => navigate("/ai/inspection")}><Statistic title="已解决" value={stats?.by_status?.resolved || 0} prefix={<CheckCircleOutlined />} valueStyle={{ color: "#3f8600" }} /></Card></Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={14}><Card title="告警趋势"><ReactEChartsCore option={trendOption} style={{ height: 260 }} /></Card></Col>
        <Col xs={24} lg={10}><Card title="最近告警" extra={<a onClick={() => navigate("/monitoring/alerts")}>全部</a>}>
          <Table columns={alertColumns} dataSource={alerts?.items?.slice(0, 5) || []} rowKey="id" size="small" pagination={false} /></Card></Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        {[
          { icon: <DesktopOutlined />, label: "设备管理", path: "/asset" },
          { icon: <AlertOutlined />, label: "告警监控", path: "/monitoring/alerts" },
          { icon: <NodeIndexOutlined />, label: "服务拓扑", path: "/apm/topology" },
          { icon: <RobotOutlined />, label: "AI 问答", path: "/ai/chat" },
          { icon: <CheckCircleOutlined />, label: "巡检报告", path: "/ai/inspection" },
          { icon: <BookOutlined />, label: "知识库", path: "/knowledge" },
        ].map((item, i) => (
          <Col key={i} xs={12} sm={8} md={4}>
            <Card hoverable size="small" style={{ textAlign: "center" }} onClick={() => navigate(item.path)}>
              <div style={{ fontSize: 24, color: "#1677ff", marginBottom: 4 }}>{item.icon}</div>
              <Text>{item.label}</Text>
            </Card>
          </Col>
        ))}
      </Row>
    </div>
  );
}
