import { useQuery } from "@tanstack/react-query";
import { Card, Table, Tag, Typography, Space } from "antd";
import { SafetyOutlined } from "@ant-design/icons";
import client from "../../api/client";

const { Text } = Typography;
const actionLabel: Record<string, string> = { login: "登录", acknowledge_alert: "认领告警", update_alert: "更新告警", create_user: "创建用户", trigger_backup: "触发备份" };

export default function AuditLogPage() {
  const { data, isLoading } = useQuery({ queryKey: ["audit-logs"], queryFn: () => client.get("/audit?page_size=50").then((r) => r.data) });

  const columns = [
    { title: "时间", dataIndex: "created_at", key: "time", width: 170, render: (t: string) => new Date(t).toLocaleString("zh-CN") },
    { title: "操作人", dataIndex: "username", key: "user", width: 100 },
    { title: "操作", dataIndex: "action", key: "action", width: 100, render: (a: string) => actionLabel[a] || a },
    { title: "资源类型", dataIndex: "resource_type", key: "type", width: 100 },
    { title: "详情", dataIndex: "detail", key: "detail", ellipsis: true },
    { title: "IP", dataIndex: "ip_address", key: "ip", width: 130 },
  ];

  return (
    <div>
      <Card title={<Space><SafetyOutlined />操作审计日志 (I9.5)</Space>} extra={<Text type="secondary">append-only · 不可删除 · 不可修改</Text>}>
        <Table columns={columns} dataSource={data?.items || []} rowKey="id" loading={isLoading} size="middle" pagination={{ pageSize: 20 }} />
      </Card>
    </div>
  );
}
