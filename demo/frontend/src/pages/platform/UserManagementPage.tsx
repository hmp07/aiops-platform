import { useQuery } from "@tanstack/react-query";
import { Card, Table, Tag, Typography, Space } from "antd";
import { TeamOutlined } from "@ant-design/icons";
import client from "../../api/client";

const { Text } = Typography;
const roleLabel: Record<string, string> = { admin: "管理员", engineer: "运维工程师", viewer: "只读观察员" };
const roleColor: Record<string, string> = { admin: "red", engineer: "blue", viewer: "default" };

export default function UserManagementPage() {
  const { data, isLoading } = useQuery({ queryKey: ["users"], queryFn: () => client.get("/users").then((r) => r.data) });

  const columns = [
    { title: "用户名", dataIndex: "username", key: "username" },
    { title: "姓名", dataIndex: "display_name", key: "display_name" },
    { title: "邮箱", dataIndex: "email", key: "email" },
    { title: "角色", dataIndex: "role", key: "role", render: (r: string) => <Tag color={roleColor[r]}>{roleLabel[r]}</Tag> },
    { title: "状态", dataIndex: "is_active", key: "active", render: (a: boolean) => a ? <Tag color="green">启用</Tag> : <Tag color="red">禁用</Tag> },
    { title: "最后登录", dataIndex: "last_login_at", key: "last_login", render: (t: string) => t ? new Date(t).toLocaleString("zh-CN") : "-" },
  ];

  return (
    <div>
      <Card title={<Space><TeamOutlined />用户管理</Space>} extra={<Text type="secondary">演示角色: admin(管理员) / engineer(运维工程师) / viewer(只读)</Text>}>
        <Table columns={columns} dataSource={data?.items || []} rowKey="id" loading={isLoading} size="middle" pagination={false} />
      </Card>
    </div>
  );
}
