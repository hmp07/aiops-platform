import { useQuery } from "@tanstack/react-query";
import { Card, Table, Tag, Row, Col, Statistic, Progress, Typography, Space } from "antd";
import { ApartmentOutlined } from "@ant-design/icons";
import ReactEChartsCore from "echarts-for-react";
import client from "../../api/client";

const { Text, Title } = Typography;
const ipSourceLabel: Record<string, string> = { arp_discovery: "ARP 发现", manual: "人工指定" };

export default function SubnetTreePage() {
  const { data: stats } = useQuery({ queryKey: ["ipam-stats"], queryFn: () => client.get("/ipam/stats").then((r) => r.data) });
  const { data: allocs } = useQuery({ queryKey: ["allocations"], queryFn: () => client.get("/ipam/allocations?page_size=100").then((r) => r.data) });

  const pieOption = {
    tooltip: { trigger: "item" },
    series: [{
      type: "pie", radius: ["50%", "75%"], center: ["50%", "50%"],
      data: [
        { value: stats?.total_used || 0, name: "已使用", itemStyle: { color: "#1677ff" } },
        { value: (stats?.total_ips || 0) - (stats?.total_used || 0), name: "空闲", itemStyle: { color: "#d9d9d9" } },
      ],
      label: { formatter: "{b}\n{d}%" },
    }],
  };

  return (
    <div>
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={8}><Card><Statistic title="子网总数" value={stats?.total_subnets || 0} prefix={<ApartmentOutlined />} /></Card></Col>
        <Col span={8}><Card><Statistic title="IP 总数" value={stats?.total_ips || 0} /></Card></Col>
        <Col span={8}><Card><Statistic title="幽灵 IP" value={stats?.ghost_ips || 0} valueStyle={{ color: "#cf1322" }} /></Card></Col>
      </Row>

      <Row gutter={16}>
        <Col xs={24} lg={10}>
          <Card title="IP 使用分布"><ReactEChartsCore option={pieOption} style={{ height: 260 }} /></Card>
        </Col>
        <Col xs={24} lg={14}>
          <Card title="子网清单">
            {(stats?.subnets || []).map((s: any) => (
              <Card key={s.id} size="small" style={{ marginBottom: 12 }}>
                <Row justify="space-between" align="middle">
                  <Col span={8}><Text strong>{s.cidr}</Text><br /><Text type="secondary">{s.description} | VLAN {s.vlan_id}</Text></Col>
                  <Col span={6}><Text>网关: {s.gateway}</Text></Col>
                  <Col span={10}><Progress percent={Math.round((s.used_ips / s.total_ips) * 100)} size="small" strokeColor={s.used_ips / s.total_ips > 0.85 ? "#f5222d" : "#1677ff"} format={() => `${s.used_ips}/${s.total_ips}`} /></Col>
                </Row>
              </Card>
            ))}
          </Card>
        </Col>
      </Row>

      <Card title="IP 分配明细" style={{ marginTop: 16 }}>
        <Table dataSource={allocs?.items || []} rowKey="id" size="small" pagination={false}
          columns={[
            { title: "IP 地址", dataIndex: "ip_address" },
            { title: "状态", dataIndex: "status", render: (s: string) => <Tag color={s === "allocated" ? "blue" : s === "reserved" ? "orange" : "default"}>{s === "allocated" ? "已分配" : s === "reserved" ? "保留" : "空闲"}</Tag> },
            { title: "关联设备", dataIndex: "device_id", render: (d: string) => d || "-" },
            { title: "接口", dataIndex: "interface_name", render: (i: string) => i || "-" },
            { title: "来源", dataIndex: "source", render: (s: string) => ipSourceLabel[s] || s },
          ]}
        />
      </Card>
    </div>
  );
}
