import { useQuery } from "@tanstack/react-query";
import { Card, List, Tag, Typography, Spin, Button, Space } from "antd";
import { FileTextOutlined, CheckCircleOutlined, ReloadOutlined } from "@ant-design/icons";
import ReactMarkdown from "react-markdown";
import client from "../../api/client";

const { Title, Text } = Typography;

export default function InspectionPage() {
  const { data, isLoading } = useQuery({ queryKey: ["inspection-reports"], queryFn: () => client.get("/ai/inspection-reports").then((r) => r.data) });

  if (isLoading) return <Spin size="large" style={{ display: "block", margin: "200px auto" }} />;

  return (
    <div style={{ maxWidth: 1000, margin: "0 auto" }}>
      <Space style={{ marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>AI 巡检报告 (H8.1)</Title>
        <Button icon={<ReloadOutlined />}>生成新报告</Button>
      </Space>

      <Card title={<Space><FileTextOutlined />最新巡检报告</Space>} extra={<Tag color="green" icon={<CheckCircleOutlined />}>AI 自动生成</Tag>}>
        {data?.items?.[0] ? (
          <div>
            <Text type="secondary">生成时间: {new Date(data.items[0].generated_at).toLocaleString("zh-CN")}</Text>
            <div style={{ marginTop: 16, padding: 16, background: "#fafafa", borderRadius: 8, maxHeight: 500, overflowY: "auto" }}>
              <ReactMarkdown>{data.items[0].summary}</ReactMarkdown>
            </div>
          </div>
        ) : <Text type="secondary">暂无巡检报告</Text>}
      </Card>

      <Card title="历史报告" style={{ marginTop: 16 }}>
        <List
          dataSource={data?.items || []}
          renderItem={(item: any) => (
            <List.Item extra={<Tag>{item.type === "weekly" ? "周报" : "月报"}</Tag>}>
              <List.Item.Meta
                avatar={<FileTextOutlined style={{ fontSize: 24, color: "#1677ff" }} />}
                title={<a>{item.title}</a>}
                description={`生成时间: ${new Date(item.generated_at).toLocaleString("zh-CN")} | 状态: ${item.status}`}
              />
            </List.Item>
          )}
        />
      </Card>
    </div>
  );
}
