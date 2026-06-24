import { useParams, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Descriptions, Card, Tag, Button, Table, Spin, Empty, Tabs, Space, Typography } from "antd";
import { ArrowLeftOutlined } from "@ant-design/icons";
import client from "../../api/client";

const { Text } = Typography;
const statusColor: Record<string, string> = { in_use: "green", spare: "orange", retired: "default" };
const statusLabel: Record<string, string> = { in_use: "在用", spare: "备件", retired: "退役" };

export default function DeviceDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { data: device, isLoading } = useQuery({ queryKey: ["device", id], queryFn: () => client.get(`/devices/${id}`).then((r) => r.data), enabled: !!id });
  const { data: ips } = useQuery({ queryKey: ["device-ips", id], queryFn: () => client.get(`/devices/${id}/ips`).then((r) => r.data), enabled: !!id });
  const { data: alerts } = useQuery({ queryKey: ["device-alerts", id], queryFn: () => client.get(`/devices/${id}/alerts`).then((r) => r.data), enabled: !!id });

  if (isLoading) return <Spin size="large" style={{ display: "block", margin: "200px auto" }} />;
  if (!device) return <Empty description="设备不存在" />;

  return (
    <div>
      <Button icon={<ArrowLeftOutlined />} onClick={() => navigate("/asset")} style={{ marginBottom: 16 }}>返回设备列表</Button>
      <Card>
        <Descriptions title={device.device_name} bordered column={3} size="small">
          <Descriptions.Item label="类型">{device.device_type}</Descriptions.Item>
          <Descriptions.Item label="厂商">{device.vendor}</Descriptions.Item>
          <Descriptions.Item label="型号">{device.model}</Descriptions.Item>
          <Descriptions.Item label="序列号">{device.serial_number}</Descriptions.Item>
          <Descriptions.Item label="软件版本">{device.software_version}</Descriptions.Item>
          <Descriptions.Item label="管理 IP">{device.management_ip}</Descriptions.Item>
          <Descriptions.Item label="位置">{device.location}</Descriptions.Item>
          <Descriptions.Item label="机柜">{device.cabinet}</Descriptions.Item>
          <Descriptions.Item label="生命周期"><Tag color={statusColor[device.lifecycle_status]}>{statusLabel[device.lifecycle_status]}</Tag></Descriptions.Item>
          <Descriptions.Item label="所属系统">{device.business_system}</Descriptions.Item>
          <Descriptions.Item label="负责部门">{device.user_department}</Descriptions.Item>
          <Descriptions.Item label="上联设备">{device.up_link_device_id || "无"}</Descriptions.Item>
          <Descriptions.Item label="最近备份">{device.last_backup_status ? <Tag color={device.last_backup_status === "success" ? "green" : "red"}>{device.last_backup_status}</Tag> : "N/A"}</Descriptions.Item>
          <Descriptions.Item label="最近巡检">{device.last_inspection_status ? <Tag color={device.last_inspection_status === "normal" ? "green" : device.last_inspection_status === "warning" ? "orange" : "red"}>{device.last_inspection_status}</Tag> : "N/A"}</Descriptions.Item>
        </Descriptions>

        <Tabs style={{ marginTop: 16 }} items={[
          { key: "ips", label: "关联 IP", children: <Table dataSource={ips?.items || []} rowKey="id" size="small" pagination={false} columns={[{ title: "IP 地址", dataIndex: "ip_address" }, { title: "接口", dataIndex: "interface_name" }, { title: "状态", dataIndex: "status" }, { title: "来源", dataIndex: "source" }]} /> },
          { key: "alerts", label: `关联告警 (${alerts?.items?.length || 0})`, children: <Table dataSource={alerts?.items || []} rowKey="id" size="small" pagination={false} columns={[{ title: "标题", dataIndex: "title", render: (t: string, r: any) => <a onClick={() => navigate(`/monitoring/alerts/${r.id}`)}>{t}</a> }, { title: "严重级别", dataIndex: "severity" }, { title: "状态", dataIndex: "status" }]} /> },
        ]} />
      </Card>
    </div>
  );
}
