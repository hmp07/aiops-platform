import { useQuery } from "@tanstack/react-query";
import { Card, List, Tag, Input, Space, Typography, Row, Col, Statistic, Spin } from "antd";
import { BookOutlined, SearchOutlined, FileTextOutlined, ThunderboltOutlined, QuestionCircleOutlined } from "@ant-design/icons";
import ReactMarkdown from "react-markdown";
import { useState } from "react";
import client from "../../api/client";

const { Text, Title } = Typography;
const typeIcon: Record<string, React.ReactNode> = { case: <FileTextOutlined />, template: <FileTextOutlined />, emergency: <ThunderboltOutlined />, faq: <QuestionCircleOutlined /> };
const typeLabel: Record<string, string> = { case: "故障案例", template: "命令模板", emergency: "应急预案", faq: "FAQ" };

export default function KnowledgePage() {
  const [keyword, setKeyword] = useState("");
  const [selected, setSelected] = useState<any>(null);
  const { data, isLoading } = useQuery({ queryKey: ["knowledge", keyword], queryFn: () => client.get("/knowledge/articles", { params: { keyword, page_size: 50 } }).then((r) => r.data) });
  const { data: stats } = useQuery({ queryKey: ["knowledge-stats"], queryFn: () => client.get("/knowledge/stats").then((r) => r.data) });

  return (
    <div>
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}><Card size="small"><Statistic title="知识总量" value={stats?.total || 0} prefix={<BookOutlined />} /></Card></Col>
        <Col span={6}><Card size="small"><Statistic title="故障案例" value={stats?.by_type?.case || 0} /></Card></Col>
        <Col span={6}><Card size="small"><Statistic title="应急预案" value={stats?.by_type?.emergency || 0} /></Card></Col>
        <Col span={6}><Card size="small"><Statistic title="FAQ" value={stats?.by_type?.faq || 0} /></Card></Col>
      </Row>

      <Row gutter={16}>
        <Col xs={24} lg={8}>
          <Card>
            <Input prefix={<SearchOutlined />} placeholder="搜索知识库..." value={keyword} onChange={(e) => setKeyword(e.target.value)} allowClear style={{ marginBottom: 12 }} />
            <List dataSource={data?.items || []} loading={isLoading} renderItem={(item: any) => (
              <List.Item onClick={() => setSelected(item)} style={{ cursor: "pointer" }} extra={<Tag color={item.article_type === "emergency" ? "red" : "blue"}>{typeLabel[item.article_type]}</Tag>}>
                <List.Item.Meta avatar={typeIcon[item.article_type]} title={item.title} description={<Space size={4}>{item.tags?.map((t: string) => <Tag key={t} style={{ fontSize: 11 }}>{t}</Tag>)}</Space>} />
              </List.Item>
            )} />
          </Card>
        </Col>
        <Col xs={24} lg={16}>
          {selected ? (
            <Card title={selected.title} extra={<Tag>{typeLabel[selected.article_type]}</Tag>}>
              <div style={{ maxHeight: 500, overflowY: "auto" }}>
                <ReactMarkdown>{selected.content}</ReactMarkdown>
              </div>
            </Card>
          ) : (
            <Card><Text type="secondary">请从左侧选择知识库文章查看详情</Text></Card>
          )}
        </Col>
      </Row>
    </div>
  );
}
