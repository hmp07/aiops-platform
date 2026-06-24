import { useParams, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Descriptions, Tag, Card, Timeline, Progress, Row, Col, Button, Space, Typography, Spin, Empty, Divider } from "antd";
import { ArrowLeftOutlined, CheckCircleOutlined, BulbOutlined, SafetyOutlined } from "@ant-design/icons";
import ReactMarkdown from "react-markdown";
import client from "../../api/client";

const { Title, Text, Paragraph } = Typography;

const severityColor: Record<string, string> = { critical: "red", warning: "orange", info: "blue" };
const statusLabel: Record<string, string> = { triggered: "待处理", acknowledged: "已认领", in_progress: "处理中", resolved: "已解决", closed: "已关闭", suppressed: "已压制" };

export default function AlertDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { data: alert, isLoading } = useQuery({ queryKey: ["alert", id], queryFn: () => client.get(`/alerts/${id}`).then((r) => r.data), enabled: !!id });

  if (isLoading) return <Spin size="large" style={{ display: "block", margin: "200px auto" }} />;
  if (!alert) return <Empty description="未找到告警" />;

  const rc = alert.root_cause;

  return (
    <div>
      <Button icon={<ArrowLeftOutlined />} onClick={() => navigate("/monitoring/alerts")} style={{ marginBottom: 16 }}>返回告警列表</Button>

      {/* Alert Header */}
      <Card style={{ marginBottom: 16 }}>
        <Descriptions title={<Space><Tag color={severityColor[alert.severity]}>{alert.severity === "critical" ? "严重" : alert.severity === "warning" ? "警告" : "提示"}</Tag><Title level={4} style={{ margin: 0 }}>{alert.title}</Title></Space>} column={3} size="small">
          <Descriptions.Item label="设备">{alert.device_name}</Descriptions.Item>
          <Descriptions.Item label="来源">{alert.source}</Descriptions.Item>
          <Descriptions.Item label="状态"><Tag>{statusLabel[alert.status]}</Tag></Descriptions.Item>
          <Descriptions.Item label="触发时间">{new Date(alert.time).toLocaleString("zh-CN")}</Descriptions.Item>
          <Descriptions.Item label="负责人">{alert.assigned_to ? (alert.assigned_to === "u2" ? "李运维" : "未知") : "未指派"}</Descriptions.Item>
          <Descriptions.Item label="告警规则">{alert.rule_name}</Descriptions.Item>
        </Descriptions>
        <Paragraph style={{ marginTop: 12, padding: 12, background: "#fafafa", borderRadius: 8 }}>{alert.description}</Paragraph>
      </Card>

      <Row gutter={16}>
        {/* Evidence Timeline */}
        <Col xs={24} lg={8}>
          <Card title="事件时间线" size="small" style={{ marginBottom: 16 }}>
            {alert.timeline && alert.timeline.length > 0 ? (
              <Timeline items={alert.timeline.map((t: any) => ({
                color: t.type === "alert_triggered" ? "red" : t.type === "ai_analysis" ? "blue" : t.type === "acknowledged" ? "green" : "gray",
                children: <div><Text strong>{new Date(t.time).toLocaleTimeString("zh-CN")}</Text><br /><Text type="secondary">{t.event}</Text></div>,
              }))} />
            ) : <Text type="secondary">暂无时间线</Text>}
          </Card>

          {/* Evidence */}
          {alert.evidence?.config_snapshot && (
            <Card title="取证快照" size="small" style={{ marginBottom: 16 }}>
              <Text strong>配置变更记录：</Text>
              {alert.evidence.config_snapshot.recent_changes?.map((c: any, i: number) => (
                <Card key={i} size="small" style={{ marginTop: 8 }}>
                  <Text type="secondary">{new Date(c.time).toLocaleString("zh-CN")}</Text><br />
                  <Text>{c.detail}</Text><br />
                  <Text type="secondary">操作人: {c.operator}</Text>
                </Card>
              ))}
              {alert.evidence.log_fragment && (
                <>
                  <Divider style={{ margin: "12px 0" }} />
                  <Text strong>关键日志片段：</Text>
                  {alert.evidence.log_fragment.map((log: any, i: number) => (
                    <div key={i} style={{ marginTop: 4, fontSize: 12, fontFamily: "monospace", background: "#1e1e1e", color: log.level === "CRIT" ? "#f5222d" : "#faad14", padding: "4px 8px", borderRadius: 4 }}>
                      [{log.level}] {log.message}
                    </div>
                  ))}
                </>
              )}
            </Card>
          )}
        </Col>

        {/* AI Root Cause Analysis */}
        <Col xs={24} lg={16}>
          {rc ? (
            <Card title={<Space><BulbOutlined style={{ color: "#1677ff" }} />AI 根因分析结果</Space>} style={{ marginBottom: 16 }}>
              <Paragraph style={{ padding: 12, background: "#e6f4ff", borderRadius: 8, marginBottom: 16 }}>
                <Text strong>综合结论：</Text>{rc.summary}
              </Paragraph>
              <Title level={5}>根因假设（按概率排序）</Title>
              {rc.hypotheses?.map((h: any, i: number) => (
                <Card key={i} size="small" style={{ marginBottom: 12, borderLeft: `4px solid ${i === 0 ? "#1677ff" : i === 1 ? "#fa8c16" : "#d9d9d9"}` }}>
                  <Row align="middle">
                    <Col span={4}><Progress type="circle" percent={Math.round(h.probability * 100)} size={60} strokeColor={i === 0 ? "#1677ff" : i === 1 ? "#fa8c16" : "#d9d9d9"} /></Col>
                    <Col span={20}>
                      <Text strong>#{h.rank} {h.cause}</Text>
                      <div style={{ marginTop: 8 }}>
                        <Text type="secondary">证据：</Text>
                        <ul style={{ margin: "4px 0", paddingLeft: 20 }}>
                          {h.evidence.map((e: string, j: number) => <li key={j}><Text type="secondary">{e}</Text></li>)}
                        </ul>
                      </div>
                    </Col>
                  </Row>
                </Card>
              ))}
              <Text type="secondary" style={{ fontSize: 12 }}>* 分析时间: {new Date(rc.analysis_time).toLocaleString("zh-CN")} | 数据来源: E5.3 配置变更记录 + F6.9 跨层关联数据 + G7.1 历史案例</Text>
            </Card>
          ) : (
            <Card title={<Space><BulbOutlined />AI 根因分析</Space>} style={{ marginBottom: 16 }}>
              <Empty description="该告警暂未触发 AI 根因分析。对于严重告警，分析会自动触发。查看告警 a1 和 a2 了解 AI 分析能力。" />
            </Card>
          )}

          {/* AI Cross-layer Diagnosis */}
          {id === "a2" && (
            <Card title={<Space><SafetyOutlined style={{ color: "#722ed1" }} />AI 跨层故障定界 (H8.10)</Space>} size="small" style={{ marginBottom: 16 }}>
              <Row gutter={16}>
                {[
                  { label: "应用代码层", pct: 5, color: "#52c41a" },
                  { label: "数据库层", pct: 75, color: "#f5222d" },
                  { label: "网络层", pct: 20, color: "#fa8c16" },
                  { label: "宿主机资源层", pct: 0, color: "#d9d9d9" },
                ].map((l, i) => (
                  <Col span={6} key={i} style={{ textAlign: "center" }}>
                    <Progress type="circle" percent={l.pct} size={80} strokeColor={l.color} />
                    <div style={{ marginTop: 8 }}><Text>{l.label}</Text></div>
                    <Text type="secondary" style={{ fontSize: 12 }}>{l.pct}%</Text>
                  </Col>
                ))}
              </Row>
              <Divider />
              <Text strong>定界结论：</Text>75% 概率为数据库慢查询问题（orders 表缺失索引），20% 概率为网络层问题（交换机 CRC 错误），5% 概率为应用代码问题。
            </Card>
          )}
        </Col>
      </Row>
    </div>
  );
}
