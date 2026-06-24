import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Card, List, Tag, Input, Typography, Button, Modal, Form, Select, message, Row, Col } from "antd";
import { SearchOutlined } from "@ant-design/icons";
import ReactMarkdown from "react-markdown";
import { knowledgeApi } from "../../api/modules";
const { Text } = Typography;

export default function KnowledgePage() {
  const qc = useQueryClient();
  const [keyword, setKeyword] = useState("");
  const [selected, setSelected] = useState<any>(null);
  const [open, setOpen] = useState(false);
  const [form] = Form.useForm();
  const { data, isLoading } = useQuery({ queryKey: ["knowledge", keyword], queryFn: () => keyword ? knowledgeApi.search({ keyword }).then(r => r.data) : knowledgeApi.listArticles({ page_size: 50 }).then(r => r.data) });
  const createMu = useMutation({ mutationFn: (v: any) => knowledgeApi.createArticle(v), onSuccess: () => { qc.invalidateQueries({ queryKey: ["knowledge"] }); setOpen(false); form.resetFields(); } });

  return (
    <Row gutter={16}>
      <Col xs={24} lg={8}>
        <Card extra={<Button size="small" onClick={() => setOpen(true)}>New</Button>}>
          <Input prefix={<SearchOutlined />} placeholder="Search..." value={keyword} onChange={e => setKeyword(e.target.value)} allowClear style={{ marginBottom: 12 }} />
          <List dataSource={data?.items || []} loading={isLoading} renderItem={(item: any) => (
            <List.Item onClick={() => setSelected(item)} style={{ cursor: "pointer" }} extra={<Tag>{item.article_type}</Tag>}>
              <List.Item.Meta title={item.title} description={item.tags?.join(", ")} />
            </List.Item>
          )} />
        </Card>
      </Col>
      <Col xs={24} lg={16}>
        {selected ? <Card title={selected.title} extra={<Tag>{selected.article_type}</Tag>}><ReactMarkdown>{selected.content}</ReactMarkdown></Card> : <Card><Text type="secondary">Select an article</Text></Card>}
      </Col>
      <Modal title="New Article" open={open} onCancel={() => setOpen(false)} onOk={() => form.submit()}>
        <Form form={form} layout="vertical" onFinish={v => createMu.mutate(v)}>
          <Form.Item name="title" label="Title" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="content" label="Content" rules={[{ required: true }]}><Input.TextArea rows={6} /></Form.Item>
          <Form.Item name="article_type" label="Type"><Select options={["case","template","emergency","faq"].map(s=>({value:s,label:s}))} /></Form.Item>
        </Form>
      </Modal>
    </Row>
  );
}
