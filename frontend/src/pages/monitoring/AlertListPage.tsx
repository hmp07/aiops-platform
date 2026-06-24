import { useQuery } from "@tanstack/react-query";
import { Table, Tag, Card, Statistic, Row, Col } from "antd";
import { useNavigate } from "react-router-dom";
import { alertApi } from "../../api/modules";

const severityColor: Record<string, string> = { critical: "red", warning: "orange", info: "blue" };
const statusLabel: Record<string, string> = { triggered: "待处理", acknowledged: "已认领", in_progress: "处理中", resolved: "已解决", closed: "已关闭" };

export default function AlertListPage() {
  const navigate = useNavigate();
  const { data, isLoading } = useQuery({ queryKey: ["alerts"], queryFn: () => alertApi.list({ page_size: 100 }).then(r => r.data) });
  const { data: stats } = useQuery({ queryKey: ["alert-stats"], queryFn: () => alertApi.stats().then(r => r.data) });

  const columns = [
    { title: "标题", dataIndex: "title", render: (t: string, r: any) => <a onClick={() => navigate(`/monitoring/alerts/${r.id}`)}>{t}</a> },
    { title: "级别", dataIndex: "severity", width: 70, render: (s: string) => <Tag color={severityColor[s]}>{s}</Tag> },
    { title: "状态", dataIndex: "status", width: 80, render: (s: string) => statusLabel[s] || s },
    { title: "来源", dataIndex: "source", width: 70 },
    { title: "时间", dataIndex: "time", width: 170, render: (t: string) => new Date(t).toLocaleString() },
  ];

  return (
    <div>
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col xs={8} sm={4}><Card size="small"><Statistic title="总计" value={stats?.total || 0} /></Card></Col>
        <Col xs={8} sm={4}><Card size="small"><Statistic title="严重" value={stats?.by_severity?.critical || 0} valueStyle={{ color: "#cf1322" }} /></Card></Col>
        <Col xs={8} sm={4}><Card size="small"><Statistic title="待处理" value={stats?.by_status?.triggered || 0} valueStyle={{ color: "#cf1322" }} /></Card></Col>
        <Col xs={8} sm={4}><Card size="small"><Statistic title="已解决" value={stats?.by_status?.resolved || 0} valueStyle={{ color: "#3f8600" }} /></Card></Col>
        <Col xs={8} sm={4}><Card size="small"><Statistic title="已关闭" value={stats?.by_status?.closed || 0} /></Card></Col>
        <Col xs={8} sm={4}><Card size="small"><Statistic title="压制" value={stats?.suppressed_count || 0} /></Card></Col>
      </Row>
      <Card title="告警列表">
        <Table columns={columns} dataSource={data?.items || []} rowKey="id" loading={isLoading} size="middle" pagination={{ pageSize: 20 }} />
      </Card>
    </div>
  );
}
