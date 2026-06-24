import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Table, Card, Input, Button, Tag, Space, message } from "antd";
import { SearchOutlined } from "@ant-design/icons";
import { logApi } from "../../api/modules";

const levelColor: Record<string, string> = { CRIT: "red", ERR: "red", WARN: "orange", INFO: "blue" };

export default function LogExplorerPage() {
  const qc = useQueryClient();
  const [keyword, setKeyword] = useState("");
  const { data, isLoading } = useQuery({ queryKey: ["logs", keyword], queryFn: () => logApi.list(keyword ? { keyword } : { page_size: 50 }).then(r => r.data) });
  const ingestMu = useMutation({ mutationFn: () => logApi.ingest({ messages: [{ message: `Test log ${new Date().toISOString()}`, severity: "info", hostname: "test" }] }), onSuccess: () => { qc.invalidateQueries({ queryKey: ["logs"] }); message.success("Ingested"); } });

  return (
    <Card title="Log Explorer" extra={<Button onClick={() => ingestMu.mutate()}>Ingest Test</Button>}>
      <Space style={{ marginBottom: 16 }}><Input prefix={<SearchOutlined />} placeholder="Keyword..." value={keyword} onChange={e => setKeyword(e.target.value)} allowClear style={{ width: 300 }} /></Space>
      <Table columns={[
        { title: "Time", dataIndex: "time", width: 170, render: (t: string) => new Date(t).toLocaleString() },
        { title: "Host", dataIndex: "hostname", width: 130 }, { title: "Level", dataIndex: "severity", width: 70, render: (l: string) => <Tag color={levelColor[l] || "default"}>{l}</Tag> },
        { title: "Message", dataIndex: "message", ellipsis: true },
      ]} dataSource={data?.items || []} rowKey="id" loading={isLoading} size="middle" pagination={{ pageSize: 20 }} />
    </Card>
  );
}
