import { useState, useEffect } from "react";
import { Card, Tabs, Table, Statistic, Row, Col, Tag, Space, Button, message, Popconfirm } from "antd";
import { ReloadOutlined, DashboardOutlined, MessageOutlined, ToolOutlined, RobotOutlined, ThunderboltOutlined } from "@ant-design/icons";
import * as aiopsApi from "../../api/aiops";

export default function AIOpsAuditPage() {
  const [activeTab, setActiveTab] = useState("overview");

  const tabItems = [
    { key: "overview", label: <span><DashboardOutlined /> 总览</span>, children: <OverviewTab /> },
    { key: "sessions", label: <span><MessageOutlined /> 会话</span>, children: <SessionsTab /> },
    { key: "tools", label: <span><ToolOutlined /> 工具调用</span>, children: <ToolsTab /> },
    { key: "models", label: <span><RobotOutlined /> 模型调用</span>, children: <ModelsTab /> },
    { key: "actions", label: <span><ThunderboltOutlined /> 操作</span>, children: <ActionsTab /> },
  ];

  return (
    <Card title="审计日志" style={{ height: "calc(100vh - 140px)", overflow: "auto" }}>
      <Tabs activeKey={activeTab} onChange={setActiveTab} items={tabItems} />
    </Card>
  );
}

// ── Overview Tab ──────────────────────────────────────────────

function OverviewTab() {
  const [overview, setOverview] = useState<any>({});
  const [costs, setCosts] = useState<any[]>([]);

  useEffect(() => {
    aiopsApi.getAuditOverview().then(r => setOverview(r.data)).catch(() => {});
    aiopsApi.getAuditCosts().then(r => setCosts(r.data.items || [])).catch(() => {});
  }, []);

  return (
    <div>
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}><Card><Statistic title="总会话数" value={overview.total_sessions || 0} /></Card></Col>
        <Col span={6}><Card><Statistic title="工具调用" value={overview.total_tool_invocations || 0} /></Card></Col>
        <Col span={6}><Card><Statistic title="模型调用" value={overview.total_model_invocations || 0} /></Card></Col>
        <Col span={6}><Card><Statistic title="总成本" value={overview.total_cost || 0} precision={4} prefix="$" /></Card></Col>
      </Row>

      {costs.length > 0 && (
        <Card title="模型成本分布" size="small">
          <Table dataSource={costs} rowKey="model_name" size="small" pagination={false}
            columns={[
              { title: "模型", dataIndex: "model_name", key: "model" },
              { title: "调用次数", dataIndex: "invocations", key: "count" },
              { title: "Prompt Tokens", dataIndex: "total_prompt_tokens", key: "pt" },
              { title: "Completion Tokens", dataIndex: "total_completion_tokens", key: "ct" },
              { title: "总成本", dataIndex: "total_cost", key: "cost", render: (v: number) => `$${v.toFixed(4)}` },
            ]}
          />
        </Card>
      )}
    </div>
  );
}

// ── Sessions Tab ──────────────────────────────────────────────

function SessionsTab() {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [pagination, setPagination] = useState({ current: 1, pageSize: 20, total: 0 });

  const loadData = async (page = 1) => {
    setLoading(true);
    try {
      const r = await aiopsApi.getAuditSessions({ page, page_size: pagination.pageSize });
      setData(r.data.items || []);
      setPagination(prev => ({ ...prev, current: page, total: r.data.total || 0 }));
    } catch {}
    setLoading(false);
  };
  useEffect(() => { loadData(); }, []);

  const columns = [
    { title: "标题", dataIndex: "title", key: "title", ellipsis: true },
    { title: "用户", dataIndex: "user_id", key: "user", width: 200, ellipsis: true },
    { title: "消息数", dataIndex: "message_count", key: "count", width: 80 },
    { title: "最后消息", dataIndex: "last_message_at", key: "last", width: 180, render: (v: string) => v ? new Date(v).toLocaleString() : "-" },
    { title: "创建时间", dataIndex: "created_at", key: "created", width: 180, render: (v: string) => new Date(v).toLocaleString() },
    {
      title: "操作", key: "actions", width: 80,
      render: (_: any, r: any) => (
        <Popconfirm title="删除?" onConfirm={async () => { await aiopsApi.deleteAuditSession(r.id); loadData(); }}>
          <Button size="small" danger>删除</Button>
        </Popconfirm>
      ),
    },
  ];

  return (
    <div>
      <Button icon={<ReloadOutlined />} onClick={() => loadData()} style={{ marginBottom: 16 }}>刷新</Button>
      <Table dataSource={data} columns={columns} rowKey="id" loading={loading} size="small"
        pagination={{ ...pagination, onChange: loadData }} />
    </div>
  );
}

// ── Tools Tab ─────────────────────────────────────────────────

function ToolsTab() {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [pagination, setPagination] = useState({ current: 1, pageSize: 20, total: 0 });

  const loadData = async (page = 1) => {
    setLoading(true);
    try {
      const r = await aiopsApi.getAuditToolInvocations({ page, page_size: pagination.pageSize });
      setData(r.data.items || []);
      setPagination(prev => ({ ...prev, current: page, total: r.data.total || 0 }));
    } catch {}
    setLoading(false);
  };
  useEffect(() => { loadData(); }, []);

  const columns = [
    { title: "工具名", dataIndex: "tool_name", key: "tool", width: 180 },
    { title: "会话", dataIndex: "session_id", key: "session", width: 200, ellipsis: true },
    { title: "参数", dataIndex: "input_params", key: "params", ellipsis: true, render: (v: any) => JSON.stringify(v).slice(0, 80) },
    { title: "结果摘要", dataIndex: "output_summary", key: "summary", ellipsis: true },
    { title: "延迟", dataIndex: "latency_ms", key: "latency", width: 80, render: (v: number) => `${v}ms` },
    { title: "状态", dataIndex: "status", key: "status", width: 80, render: (v: string) => <Tag color={v === "success" ? "green" : "red"}>{v}</Tag> },
    { title: "时间", dataIndex: "created_at", key: "time", width: 180, render: (v: string) => new Date(v).toLocaleString() },
  ];

  return (
    <div>
      <Button icon={<ReloadOutlined />} onClick={() => loadData()} style={{ marginBottom: 16 }}>刷新</Button>
      <Table dataSource={data} columns={columns} rowKey="id" loading={loading} size="small"
        pagination={{ ...pagination, onChange: loadData }} />
    </div>
  );
}

// ── Models Tab ────────────────────────────────────────────────

function ModelsTab() {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [pagination, setPagination] = useState({ current: 1, pageSize: 20, total: 0 });

  const loadData = async (page = 1) => {
    setLoading(true);
    try {
      const r = await aiopsApi.getAuditModelInvocations({ page, page_size: pagination.pageSize });
      setData(r.data.items || []);
      setPagination(prev => ({ ...prev, current: page, total: r.data.total || 0 }));
    } catch {}
    setLoading(false);
  };
  useEffect(() => { loadData(); }, []);

  const columns = [
    { title: "模型", dataIndex: "model_name", key: "model" },
    { title: "用途", dataIndex: "purpose", key: "purpose", width: 100 },
    { title: "Prompt Tokens", dataIndex: "prompt_tokens", key: "pt", width: 100 },
    { title: "Comp Tokens", dataIndex: "completion_tokens", key: "ct", width: 100 },
    { title: "成本", dataIndex: "total_cost", key: "cost", width: 100, render: (v: number) => `$${(v || 0).toFixed(4)}` },
    { title: "延迟", dataIndex: "latency_ms", key: "latency", width: 80, render: (v: number) => `${v}ms` },
    { title: "时间", dataIndex: "created_at", key: "time", width: 180, render: (v: string) => new Date(v).toLocaleString() },
  ];

  return (
    <div>
      <Button icon={<ReloadOutlined />} onClick={() => loadData()} style={{ marginBottom: 16 }}>刷新</Button>
      <Table dataSource={data} columns={columns} rowKey="id" loading={loading} size="small"
        pagination={{ ...pagination, onChange: loadData }} />
    </div>
  );
}

// ── Actions Tab ───────────────────────────────────────────────

function ActionsTab() {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [pagination, setPagination] = useState({ current: 1, pageSize: 20, total: 0 });

  const loadData = async (page = 1) => {
    setLoading(true);
    try {
      const r = await aiopsApi.getAuditActions({ page, page_size: pagination.pageSize });
      setData(r.data.items || []);
      setPagination(prev => ({ ...prev, current: page, total: r.data.total || 0 }));
    } catch {}
    setLoading(false);
  };
  useEffect(() => { loadData(); }, []);

  const columns = [
    { title: "标题", dataIndex: "title", key: "title", ellipsis: true },
    { title: "类型", dataIndex: "action_type", key: "type", width: 120 },
    { title: "风险等级", dataIndex: "risk_level", key: "risk", width: 80, render: (v: string) => <Tag>{v}</Tag> },
    { title: "状态", dataIndex: "status", key: "status", width: 100, render: (v: string) => {
      const color = v === "confirmed" ? "green" : v === "canceled" ? "red" : v === "executed" ? "blue" : "orange";
      return <Tag color={color}>{v}</Tag>;
    }},
    { title: "创建时间", dataIndex: "created_at", key: "time", width: 180, render: (v: string) => new Date(v).toLocaleString() },
  ];

  return (
    <div>
      <Button icon={<ReloadOutlined />} onClick={() => loadData()} style={{ marginBottom: 16 }}>刷新</Button>
      <Table dataSource={data} columns={columns} rowKey="id" loading={loading} size="small"
        pagination={{ ...pagination, onChange: loadData }} />
    </div>
  );
}
