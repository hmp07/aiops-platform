import { useQuery } from "@tanstack/react-query";
import { Card, Table, Tag, Typography, Spin, Space } from "antd";
import { CheckCircleOutlined, FileTextOutlined } from "@ant-design/icons";
import { aiApi } from "../../api/modules";
const { Title } = Typography;

export default function InspectionPage() {
  const { data: skills, isLoading } = useQuery({ queryKey: ["skills"], queryFn: () => aiApi.listSkills().then(r => r.data) });
  if (isLoading) return <Spin size="large" style={{ display: "block", margin: "200px auto" }} />;
  return (
    <div style={{ maxWidth: 1000, margin: "0 auto" }}>
      <Space style={{ marginBottom: 16 }}><Title level={4} style={{ margin: 0 }}>AI Skills (H8.1 Inspection)</Title><Tag color="green" icon={<CheckCircleOutlined />}>Available: {skills?.length || 0}</Tag></Space>
      <Card title={<Space><FileTextOutlined />Registered Skills</Space>}>
        <Table dataSource={skills || []} rowKey="skill_id" pagination={false} columns={[
          { title: "Skill ID", dataIndex: "skill_id" }, { title: "Name", dataIndex: "name" },
          { title: "Category", dataIndex: "category" }, { title: "Risk", dataIndex: "risk_level", render: (r: string) => <Tag color={r==="read_only"?"green":"orange"}>{r}</Tag> },
          { title: "Tools", dataIndex: "allowed_tools", render: (t: string[]) => t?.join(", ") || "-" },
        ]} />
      </Card>
    </div>
  );
}
