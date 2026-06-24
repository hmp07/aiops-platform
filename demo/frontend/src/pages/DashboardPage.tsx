import { useQuery } from "@tanstack/react-query";
import { Row, Col, Card, Statistic, Table, Tag, Spin, Typography } from "antd";
import { DesktopOutlined, AlertOutlined, NodeIndexOutlined, CheckCircleOutlined, WarningOutlined, CloseCircleOutlined, RobotOutlined, BookOutlined } from "@ant-design/icons";
import ReactEChartsCore from "echarts-for-react";
import { useNavigate } from "react-router-dom";
import client from "../api/client";

const { Text } = Typography;

const severityColor: Record<string, string> = { critical: "red", warning: "orange", info: "blue" };
const statusLabel: Record<string, string> = { triggered: "待处理", acknowledged: "已认领", in_progress: "处理中", resolved: "已解决", closed: "已关闭", suppressed: "已压制" };

export default function DashboardPage() {
  const navigate = useNavigate();
  const { data: stats, isLoading } = useQuery({ queryKey: ["dashboard-stats"], queryFn: () => client.get("/dashboard/stats").then((r) => r.data) });
  const { data: trend } = useQuery({ queryKey: ["alert-trend"], queryFn: () => client.get("/dashboard/alert-trend").then((r) => r.data) });
  const { data: recent } = useQuery({ queryKey: ["recent-alerts"], queryFn: () => client.get("/dashboard/recent-alerts?limit=5").then((r) => r.data) });

  if (isLoading) return <Spin size="large" style={{ display: "block", margin: "200px auto" }} />;

  const trendOption = {
    tooltip: { trigger: "axis" },
    legend: { bottom: 0 },
    grid: { left: 40, right: 20, top: 20, bottom: 40 },
    xAxis: { type: "category", data: trend?.categories || [] },
    yAxis: { type: "value" },
    series: (trend?.series || []).map((s: any) => ({ name: s.name, type: "line", data: s.data, smooth: true, lineStyle: { width: 2 }, itemStyle: { color: s.color } })),
  };

  const alertColumns = [
    { title: "告警标题", dataIndex: "title", key: "title", ellipsis: true, render: (t: string, r: any) => <a onClick={() => navigate(`/monitoring/alerts/${r.id}`)}>{t}</a> },
    { title: "严重级别", dataIndex: "severity", key: "severity", width: 90, render: (s: string) => <Tag color={severityColor[s]}>{s}</Tag> },
    { title: "状态", dataIndex: "status", key: "status", width: 80, render: (s: string) => statusLabel[s] },
    { title: "设备", dataIndex: "device_name", key: "device", width: 130 },
  ];

  return (
    <div>
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}><Card hoverable><Statistic title="设备总数" value={stats?.total_devices || 0} prefix={<DesktopOutlined />} suffix={<Text type="secondary">/ {stats?.online_devices || 0} 在线</Text>} /></Card></Col>
        <Col xs={24} sm={12} lg={6}><Card hoverable onClick={() => navigate("/monitoring/alerts")}><Statistic title="活跃告警" value={stats?.active_alerts || 0} prefix={<AlertOutlined />} suffix={<Text type="danger">/ {stats?.critical_alerts || 0} 严重</Text>} valueStyle={{ color: stats?.critical_alerts > 0 ? "#cf1322" : undefined }} /></Card></Col>
        <Col xs={24} sm={12} lg={6}><Card hoverable onClick={() => navigate("/apm/services")}><Statistic title="应用服务" value={stats?.total_services || 0} prefix={<NodeIndexOutlined />} suffix={<Text type="warning">/ {stats?.unhealthy_services || 0} 异常</Text>} /></Card></Col>
        <Col xs={24} sm={12} lg={6}><Card hoverable onClick={() => navigate("/ai/inspection")}><Statistic title="最近巡检" value={stats?.inspection_status === "completed" ? "已完成" : "未完成"} prefix={<CheckCircleOutlined />} valueStyle={{ color: "#3f8600" }} /></Card></Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={14}>
          <Card title="告警趋势（近 7 天）">
            <ReactEChartsCore option={trendOption} style={{ height: 280 }} />
          </Card>
        </Col>
        <Col xs={24} lg={10}>
          <Card title="最近告警" extra={<a onClick={() => navigate("/monitoring/alerts")}>查看全部</a>}>
            <Table columns={alertColumns} dataSource={recent?.items || []} rowKey="id" size="small" pagination={false} scroll={{ x: 400 }} />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col span={24}>
          <Card title="快速入口">
            <Row gutter={16}>
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
                    <div style={{ fontSize: 24, color: "#1677ff", marginBottom: 8 }}>{item.icon}</div>
                    <Text>{item.label}</Text>
                  </Card>
                </Col>
              ))}
            </Row>
          </Card>
        </Col>
      </Row>
    </div>
  );
}
