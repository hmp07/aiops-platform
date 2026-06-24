import { useQuery } from "@tanstack/react-query";
import { Table, Tag, Select, Space, Card, Typography, Input } from "antd";
import { useNavigate } from "react-router-dom";
import { DesktopOutlined, CloudServerOutlined, SafetyOutlined, WifiOutlined } from "@ant-design/icons";
import client from "../../api/client";

const { Text } = Typography;

const typeIcon: Record<string, React.ReactNode> = { switch: <WifiOutlined />, router: <WifiOutlined />, firewall: <SafetyOutlined />, server: <CloudServerOutlined /> };
const statusColor: Record<string, string> = { in_use: "green", spare: "orange", retired: "default" };
const statusLabel: Record<string, string> = { in_use: "在用", spare: "备件", retired: "退役" };
const backupColor: Record<string, string> = { success: "green", failed: "red" };

export default function DeviceListPage() {
  const navigate = useNavigate();
  const { data, isLoading } = useQuery({ queryKey: ["devices"], queryFn: () => client.get("/devices?page_size=50").then((r) => r.data) });

  const columns = [
    { title: "设备名称", dataIndex: "device_name", key: "name", render: (t: string, r: any) => <a onClick={() => navigate(`/asset/${r.id}`)}><Space>{typeIcon[r.device_type]}{t}</Space></a> },
    { title: "类型", dataIndex: "device_type", key: "type", width: 80 },
    { title: "厂商", dataIndex: "vendor", key: "vendor", width: 80 },
    { title: "型号", dataIndex: "model", key: "model", width: 160, ellipsis: true },
    { title: "管理 IP", dataIndex: "management_ip", key: "ip", width: 130 },
    { title: "位置", dataIndex: "location", key: "location", width: 140, ellipsis: true },
    { title: "状态", dataIndex: "lifecycle_status", key: "status", width: 80, render: (s: string) => <Tag color={statusColor[s]}>{statusLabel[s]}</Tag> },
    { title: "业务系统", dataIndex: "business_system", key: "biz", width: 100, ellipsis: true },
    { title: "最近备份", dataIndex: "last_backup_status", key: "backup", width: 90, render: (s: string) => s ? <Tag color={backupColor[s]}>{s === "success" ? "成功" : "失败"}</Tag> : <Tag>N/A</Tag> },
  ];

  return (
    <div>
      <Card title={<Space><DesktopOutlined />设备资产管理</Space>} extra={<Text type="secondary">共 {data?.total || 0} 台设备</Text>}>
        <Table columns={columns} dataSource={data?.items || []} rowKey="id" loading={isLoading} size="middle" pagination={{ pageSize: 20 }} />
      </Card>
    </div>
  );
}
