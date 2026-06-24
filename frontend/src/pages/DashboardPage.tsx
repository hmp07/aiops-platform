import { Row, Col, Card, Statistic } from "antd";
import { DesktopOutlined, AlertOutlined, NodeIndexOutlined, CheckCircleOutlined } from "@ant-design/icons";

export default function DashboardPage() {
  return (
    <div>
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic title="设备总数" value={128} prefix={<DesktopOutlined />} />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic title="活跃告警" value={5} prefix={<AlertOutlined />} valueStyle={{ color: "#cf1322" }} />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic title="在线服务" value={42} prefix={<NodeIndexOutlined />} valueStyle={{ color: "#3f8600" }} />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic title="今日巡检" value="已完成" prefix={<CheckCircleOutlined />} valueStyle={{ color: "#3f8600" }} />
          </Card>
        </Col>
      </Row>
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col span={24}>
          <Card title="概览">
            <p>欢迎使用 AIOps Platform —— AI 智能运维管理平台。请从左侧导航选择功能模块。</p>
          </Card>
        </Col>
      </Row>
    </div>
  );
}
