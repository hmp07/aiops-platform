import { useQuery } from "@tanstack/react-query";
import { Table, Card, Tag } from "antd";
import { platformApi } from "../../api/modules";
const roleColor: Record<string, string> = { admin: "red", engineer: "blue", viewer: "default" };

export default function UserManagementPage() {
  const { data, isLoading } = useQuery({ queryKey: ["users"], queryFn: () => platformApi.listUsers().then(r => r.data) });
  return (
    <Card title="User Management">
      <Table columns={[
        { title: "Username", dataIndex: "username" }, { title: "Name", dataIndex: "display_name" }, { title: "Email", dataIndex: "email" },
        { title: "Role", dataIndex: "role", render: (r: string) => <Tag color={roleColor[r]}>{r}</Tag> },
        { title: "Active", dataIndex: "is_active", render: (a: boolean) => a ? <Tag color="green">Yes</Tag> : <Tag color="red">No</Tag> },
        { title: "Last Login", dataIndex: "last_login_at", render: (t: string) => t ? new Date(t).toLocaleString() : "-" },
      ]} dataSource={data?.items || []} rowKey="id" loading={isLoading} size="middle" pagination={false} />
    </Card>
  );
}
