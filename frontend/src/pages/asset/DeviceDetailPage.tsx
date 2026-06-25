import { useParams, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Descriptions, Card, Tag, Button, Space, Spin, Empty, Row, Col, Table, Typography } from "antd";
import { ArrowLeftOutlined, DashboardOutlined, HddOutlined, CloudServerOutlined, ApiOutlined, WarningOutlined } from "@ant-design/icons";
import ReactEChartsCore from "echarts-for-react";
import { deviceApi, metricsApi } from "../../api/modules";
import "./MonitoringDashboard.css";

const { Text } = Typography;

const SEVERITY_COLOR: Record<string, string> = {
  critical: "#f5222d", warning: "#fa8c16", info: "#1890ff",
};
const STATUS_LABEL: Record<string, string> = {
  triggered: "触发中", acknowledged: "已认领", resolved: "已解决", closed: "已关闭", suppressed: "已压制",
};

/* ── tiny helpers ── */
function pct(v: number | null | undefined): number {
  if (v == null) return 0;
  return Math.min(Math.max(v, 0), 100);
}

/* ── KPI card ── */
function KpiCard({ label, value, unit, progress, color, icon }: {
  label: string; value: number | null | undefined; unit: string;
  progress: number; color: string; icon: React.ReactNode;
}) {
  return (
    <div className="kpi-card">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <span className="kpi-label">{label}</span>
        <span style={{ color, fontSize: 18 }}>{icon}</span>
      </div>
      {value != null ? (
        <>
          <div style={{ display: "flex", alignItems: "baseline", marginTop: 6 }}>
            <span className="kpi-value">{value}</span>
            <span className="kpi-unit">{unit}</span>
          </div>
          <div className="kpi-progress">
            <div className="kpi-progress-fill" style={{ width: `${pct(progress)}%`, background: color }} />
          </div>
        </>
      ) : (
        <div style={{ color: "var(--md-text-dim)", fontSize: 14, marginTop: 8 }}>--</div>
      )}
    </div>
  );
}

/* ── build ECharts trend option ── */
function buildTrendOption(trends: any) {
  if (!trends || !trends.cpu?.length) return null;
  const times = trends.cpu.map((p: any) => {
    const d = new Date((p.clock as number) * 1000);
    return `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
  });
  return {
    tooltip: {
      trigger: "axis" as const,
      backgroundColor: "rgba(5,8,15,0.92)",
      borderColor: "rgba(0,229,255,0.25)",
      textStyle: { color: "#e0e6ed", fontSize: 12 },
    },
    legend: {
      data: ["CPU", "Memory", "Disk"],
      textStyle: { color: "#8892a4", fontSize: 11 },
      bottom: 0,
    },
    grid: { left: 50, right: 20, top: 16, bottom: 36 },
    xAxis: {
      type: "category" as const,
      data: times,
      axisLabel: { color: "#8892a4", fontSize: 10 },
      axisLine: { lineStyle: { color: "rgba(0,229,255,0.12)" } },
      splitLine: { show: false },
    },
    yAxis: {
      type: "value" as const,
      max: 100,
      axisLabel: { color: "#8892a4", fontSize: 10, formatter: "{value}%" },
      splitLine: { lineStyle: { color: "rgba(255,255,255,0.05)" } },
    },
    series: [
      {
        name: "CPU", type: "line", data: trends.cpu.map((p: any) => p.value),
        smooth: true, showSymbol: false,
        lineStyle: { width: 2, color: "#00e5ff" },
        areaStyle: { color: "rgba(0,229,255,0.08)" },
        itemStyle: { color: "#00e5ff" },
      },
      {
        name: "Memory", type: "line", data: (trends.memory || []).map((p: any) => p.value),
        smooth: true, showSymbol: false,
        lineStyle: { width: 2, color: "#00ff88" },
        areaStyle: { color: "rgba(0,255,136,0.08)" },
        itemStyle: { color: "#00ff88" },
      },
      {
        name: "Disk", type: "line", data: (trends.disk || []).map((p: any) => p.value),
        smooth: true, showSymbol: false,
        lineStyle: { width: 2, color: "#ffd700" },
        areaStyle: { color: "rgba(255,215,0,0.08)" },
        itemStyle: { color: "#ffd700" },
      },
    ],
  };
}

/* ── main component ── */
export default function DeviceDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();

  const { data: device, isLoading } = useQuery({
    queryKey: ["device", id], queryFn: () => deviceApi.get(id!).then(r => r.data), enabled: !!id,
  });

  const { data: metrics } = useQuery({
    queryKey: ["device-metrics", id],
    queryFn: () => metricsApi.getDeviceMetrics(id!).then((r: any) => r.data),
    enabled: !!id,
    refetchInterval: 60_000,
  });

  const { data: alertsData } = useQuery({
    queryKey: ["device-alerts", id],
    queryFn: () => metricsApi.getDeviceAlerts(id!, { page_size: 10 }).then((r: any) => r.data),
    enabled: !!id,
  });

  /* ── loading / empty ── */
  if (isLoading) return <Spin size="large" style={{ display: "block", margin: "200px auto" }} />;
  if (!device) return <Empty description="设备不存在" />;

  const isMonitored = metrics?.monitored === true;
  const kpi = metrics?.kpi || {};
  const trends = metrics?.trends || {};
  const trendOption = buildTrendOption(trends);
  const alerts: any[] = alertsData?.alerts || [];

  const alertColumns = [
    { title: "时间", dataIndex: "time", key: "time", width: 150, render: (t: string) => new Date(t).toLocaleString() },
    { title: "级别", dataIndex: "severity", key: "severity", width: 70, render: (s: string) => <Tag color={SEVERITY_COLOR[s] || "default"}>{s}</Tag> },
    { title: "标题", dataIndex: "title", key: "title", ellipsis: true },
    { title: "状态", dataIndex: "status", key: "status", width: 72, render: (s: string) => STATUS_LABEL[s] || s },
  ];

  return (
    <div>
      <Button icon={<ArrowLeftOutlined />} onClick={() => navigate("/asset")} style={{ marginBottom: 16 }}>
        返回设备列表
      </Button>

      {/* ═══ existing CMDB info card — unchanged ═══ */}
      <Card>
        <Descriptions title={device.device_name} bordered column={3} size="small">
          <Descriptions.Item label="类型">{device.device_type}</Descriptions.Item>
          <Descriptions.Item label="厂商">{device.vendor}</Descriptions.Item>
          <Descriptions.Item label="型号">{device.model}</Descriptions.Item>
          <Descriptions.Item label="序列号">{device.serial_number || "-"}</Descriptions.Item>
          <Descriptions.Item label="软件版本">{device.software_version || "-"}</Descriptions.Item>
          <Descriptions.Item label="管理IP">{device.management_ip || "-"}</Descriptions.Item>
          <Descriptions.Item label="位置">{device.location || "-"}</Descriptions.Item>
          <Descriptions.Item label="生命周期"><Tag>{device.lifecycle_status}</Tag></Descriptions.Item>
          <Descriptions.Item label="业务系统">{device.business_system || "-"}</Descriptions.Item>
          <Descriptions.Item label="部门">{device.user_department || "-"}</Descriptions.Item>
          <Descriptions.Item label="最近备份">{device.last_backup_status || "-"}</Descriptions.Item>
          <Descriptions.Item label="最近巡检">{device.last_inspection_status || "-"}</Descriptions.Item>
        </Descriptions>
      </Card>

      {/* ═══ monitoring dashboard (ITOps-Watch style) ═══ */}
      <div style={{ marginTop: 24 }} className="monitoring-dashboard">
        {isMonitored ? (
          <>
            {/* ── KPI cards row ── */}
            <Row gutter={[12, 12]}>
              <Col xs={12} sm={6}>
                <KpiCard label="CPU" value={kpi.cpu} unit="%" progress={pct(kpi.cpu)} color="var(--md-primary)" icon={<DashboardOutlined />} />
              </Col>
              <Col xs={12} sm={6}>
                <KpiCard label="Memory" value={kpi.memory} unit="%" progress={pct(kpi.memory)} color="var(--md-green)" icon={<HddOutlined />} />
              </Col>
              <Col xs={12} sm={6}>
                <KpiCard label="Disk" value={kpi.disk} unit="%" progress={pct(kpi.disk)} color="var(--md-yellow)" icon={<CloudServerOutlined />} />
              </Col>
              <Col xs={12} sm={6}>
                <Space direction="vertical" style={{ width: "100%" }}>
                  <KpiCard label="Network ↓" value={kpi.network_in} unit="Mbps" progress={0} color="var(--md-red)" icon={<ApiOutlined />} />
                  <KpiCard label="Network ↑" value={kpi.network_out} unit="Mbps" progress={0} color="var(--md-red)" icon={<ApiOutlined />} />
                </Space>
              </Col>
            </Row>

            {/* ── Trend chart ── */}
            {trendOption && (
              <div className="chart-panel">
                <div className="panel-title">Resource Trend</div>
                <div className="panel-subtitle">Last 60 minutes</div>
                <ReactEChartsCore option={trendOption} style={{ height: 280 }} />
              </div>
            )}
          </>
        ) : (
          <div className="md-empty">
            <WarningOutlined className="md-empty-icon" />
            <div>此设备未配置 Zabbix 监控数据</div>
            <Text type="secondary" style={{ fontSize: 12 }}>No Zabbix monitoring configured for this device</Text>
          </div>
        )}
      </div>

      {/* ═══ recent alerts ═══ */}
      {alerts.length > 0 && (
        <Card title="最近告警" size="small" style={{ marginTop: 16 }}
          extra={<a onClick={() => navigate("/monitoring/alerts")}>全部</a>}>
          <Table columns={alertColumns} dataSource={alerts} rowKey="id" size="small" pagination={false} />
        </Card>
      )}
    </div>
  );
}
