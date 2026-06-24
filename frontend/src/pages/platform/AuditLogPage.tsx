import { useQuery } from "@tanstack/react-query";
import { Table, Card } from "antd";
import { platformApi } from "../../api/modules";

export default function AuditLogPage() {
  const { data, isLoading } = useQuery({ queryKey: ["audit"], queryFn: () => platformApi.listAudit({ page_size: 100 }).then(r => r.data) });
  return (
    <Card title="Audit Logs">
      <Table columns={[
        { title: "Time", dataIndex: "created_at", width: 170, render: (t: string) => new Date(t).toLocaleString() },
        { title: "User", dataIndex: "username", width: 100 }, { title: "Action", dataIndex: "action", width: 120 },
        { title: "Resource", dataIndex: "resource_type", width: 100 }, { title: "Detail", dataIndex: "detail", ellipsis: true },
        { title: "IP", dataIndex: "ip_address", width: 120 },
      ]} dataSource={data?.items || []} rowKey="id" loading={isLoading} size="middle" pagination={{ pageSize: 20 }} />
    </Card>
  );
}
