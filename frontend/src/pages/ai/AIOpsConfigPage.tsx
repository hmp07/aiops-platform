import { useState, useEffect } from "react";
import { Card, Tabs, Table, Button, Modal, Form, Input, Select, Switch, Tag, Space, message, Popconfirm, Descriptions } from "antd";
import { PlusOutlined, ReloadOutlined, ApiOutlined, ThunderboltOutlined, SettingOutlined, RobotOutlined, ToolOutlined } from "@ant-design/icons";
import * as aiopsApi from "../../api/aiops";

const { TextArea } = Input;

export default function AIOpsConfigPage() {
  const [activeTab, setActiveTab] = useState("strategy");

  const tabItems = [
    { key: "strategy", label: <span><SettingOutlined /> 策略</span>, children: <StrategyTab /> },
    { key: "skill", label: <span><ThunderboltOutlined /> Skill</span>, children: <SkillTab /> },
    { key: "mcp", label: <span><ApiOutlined /> MCP</span>, children: <MCPTab /> },
    { key: "model", label: <span><RobotOutlined /> 模型</span>, children: <ModelTab /> },
    { key: "action", label: <span><ToolOutlined /> Action</span>, children: <ActionTab /> },
  ];

  return (
    <Card title="智能体配置" style={{ height: "calc(100vh - 140px)", overflow: "auto" }}>
      <Tabs activeKey={activeTab} onChange={setActiveTab} items={tabItems} />
    </Card>
  );
}

// ── Strategy Tab ──────────────────────────────────────────────

function StrategyTab() {
  const [config, setConfig] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => { loadConfig(); }, []);

  const loadConfig = async () => {
    setLoading(true);
    try {
      const r = await aiopsApi.getConfig();
      setConfig(r.data);
    } catch { message.error("加载配置失败"); }
    setLoading(false);
  };

  const saveConfig = async (values: any) => {
    try {
      await aiopsApi.updateConfig(values);
      message.success("配置已保存");
      loadConfig();
    } catch { message.error("保存失败"); }
  };

  if (!config) return null;

  return (
    <div>
      <Form layout="vertical" initialValues={config} onFinish={saveConfig} style={{ maxWidth: 800 }}>
        <Form.Item name="system_prompt" label="System Prompt">
          <TextArea rows={4} placeholder="系统提示词..." />
        </Form.Item>
        <Form.Item name="welcome_message" label="欢迎消息">
          <Input placeholder="欢迎消息..." />
        </Form.Item>
        <Form.Item name="suggested_questions" label="建议问题（每行一个）"
          getValueFromEvent={(e: any) => e.target.value.split("\n").filter(Boolean)}
          getValueProps={(v: any) => ({ value: Array.isArray(v) ? v.join("\n") : "" })}>
          <TextArea rows={4} placeholder="建议问题..." />
        </Form.Item>
        <Space>
          <Form.Item name="allow_action_execution" label="允许执行动作" valuePropName="checked">
            <Switch />
          </Form.Item>
          <Form.Item name="require_confirmation" label="需要确认" valuePropName="checked">
            <Switch />
          </Form.Item>
          <Form.Item name="show_evidence" label="显示证据" valuePropName="checked">
            <Switch />
          </Form.Item>
        </Space>
        <Form.Item name="max_history_messages" label="最大历史消息数">
          <Input type="number" style={{ width: 100 }} />
        </Form.Item>
        <Button type="primary" htmlType="submit">保存配置</Button>
      </Form>
    </div>
  );
}

// ── Skill Tab ─────────────────────────────────────────────────

function SkillTab() {
  const [skills, setSkills] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [form] = Form.useForm();

  const loadSkills = async () => {
    setLoading(true);
    try { const r = await aiopsApi.getSkills(); setSkills(r.data.items || []); } catch {}
    setLoading(false);
  };
  useEffect(() => { loadSkills(); }, []);

  const handleCreate = async (values: any) => {
    try {
      await aiopsApi.createSkill(values);
      message.success("Skill 已创建");
      setModalOpen(false); form.resetFields(); loadSkills();
    } catch { message.error("创建失败"); }
  };

  const columns = [
    { title: "名称", dataIndex: "name", key: "name", width: 150 },
    { title: "Slug", dataIndex: "slug", key: "slug", width: 150 },
    { title: "分类", dataIndex: "category", key: "category", width: 100 },
    { title: "风险等级", dataIndex: "risk_level", key: "risk_level", width: 100, render: (v: string) => <Tag>{v}</Tag> },
    { title: "来源", dataIndex: "source_type", key: "source_type", width: 80 },
    { title: "内置", dataIndex: "is_builtin", key: "is_builtin", width: 60, render: (v: boolean) => v ? <Tag color="blue">是</Tag> : <Tag>否</Tag> },
    { title: "版本", dataIndex: "version", key: "version", width: 60 },
    {
      title: "操作", key: "actions", width: 120,
      render: (_: any, r: any) => (
        <Space>
          {!r.is_builtin && (
            <Popconfirm title="删除?" onConfirm={async () => { await aiopsApi.deleteSkill(r.id); loadSkills(); }}>
              <Button size="small" danger>删除</Button>
            </Popconfirm>
          )}
          <Button size="small" onClick={async () => { await aiopsApi.cloneSkill(r.id); message.success("已克隆"); loadSkills(); }}>克隆</Button>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>新建 Skill</Button>
        <Button icon={<ReloadOutlined />} onClick={loadSkills}>刷新</Button>
      </Space>
      <Table dataSource={skills} columns={columns} rowKey="id" loading={loading} size="small" pagination={false} />
      <Modal title="新建 Skill" open={modalOpen} onCancel={() => setModalOpen(false)} onOk={() => form.submit()}>
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Form.Item name="slug" label="Slug" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="name" label="名称" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="category" label="分类" initialValue="diagnosis"><Input /></Form.Item>
          <Form.Item name="content" label="SOP 内容"><TextArea rows={4} /></Form.Item>
          <Form.Item name="risk_level" label="风险等级" initialValue="read_only">
            <Select options={[{ value: "read_only", label: "只读" }, { value: "draft", label: "草稿" }, { value: "write", label: "写入" }, { value: "execute", label: "执行" }]} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}

// ── MCP Tab ───────────────────────────────────────────────────

function MCPTab() {
  const [servers, setServers] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const loadServers = async () => {
    setLoading(true);
    try { const r = await aiopsApi.getMcpServers(); setServers(r.data.items || []); } catch {}
    setLoading(false);
  };
  useEffect(() => { loadServers(); }, []);

  const columns = [
    { title: "名称", dataIndex: "name", key: "name" },
    { title: "类型", dataIndex: "server_type", key: "server_type", width: 80, render: (v: string) => <Tag>{v}</Tag> },
    { title: "端点", dataIndex: "endpoint_or_command", key: "endpoint", ellipsis: true },
    { title: "启用", dataIndex: "is_enabled", key: "is_enabled", width: 60, render: (v: boolean) => v ? <Tag color="green">是</Tag> : <Tag>否</Tag> },
    {
      title: "操作", key: "actions", width: 100,
      render: (_: any, r: any) => (
        <Popconfirm title="删除?" onConfirm={async () => { await aiopsApi.deleteMcpServer(r.id); loadServers(); }}>
          <Button size="small" danger>删除</Button>
        </Popconfirm>
      ),
    },
  ];

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Button icon={<ReloadOutlined />} onClick={loadServers}>刷新</Button>
      </Space>
      <Table dataSource={servers} columns={columns} rowKey="id" loading={loading} size="small" pagination={false} />
    </div>
  );
}

// ── Model Tab ─────────────────────────────────────────────────

function ModelTab() {
  const [providers, setProviders] = useState<any[]>([]);
  const [presets, setPresets] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [form] = Form.useForm();

  const loadData = async () => {
    setLoading(true);
    try {
      const [pr, ps] = await Promise.all([aiopsApi.getProviders(), aiopsApi.getProviderPresets()]);
      setProviders(pr.data.items || []);
      setPresets(ps.data.presets || []);
    } catch {}
    setLoading(false);
  };
  useEffect(() => { loadData(); }, []);

  const handleCreate = async (values: any) => {
    try {
      await aiopsApi.createProvider(values);
      message.success("Provider 已创建");
      setModalOpen(false); form.resetFields(); loadData();
    } catch { message.error("创建失败"); }
  };

  const columns = [
    { title: "名称", dataIndex: "name", key: "name" },
    { title: "类型", dataIndex: "provider_type", key: "type", width: 120, render: (v: string) => <Tag>{v}</Tag> },
    { title: "模型", dataIndex: "default_model", key: "model" },
    { title: "启用", dataIndex: "is_enabled", key: "enabled", width: 60, render: (v: boolean) => v ? <Tag color="green">是</Tag> : <Tag>否</Tag> },
    {
      title: "操作", key: "actions", width: 200,
      render: (_: any, r: any) => (
        <Space>
          <Button size="small" onClick={async () => {
            try { await aiopsApi.testProvider(r.id); message.success("连接成功"); } catch { message.error("连接失败"); }
          }}>测试</Button>
          <Popconfirm title="删除?" onConfirm={async () => { await aiopsApi.deleteProvider(r.id); loadData(); }}>
            <Button size="small" danger>删除</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>新建 Provider</Button>
        <Button icon={<ReloadOutlined />} onClick={loadData}>刷新</Button>
      </Space>

      {/* Preset cards */}
      {presets.length > 0 && (
        <div style={{ marginBottom: 16 }}>
          <div style={{ fontWeight: "bold", marginBottom: 8 }}>预设模板（点击自动填充）</div>
          <Space wrap>
            {presets.map((p: any) => (
              <Button key={p.key} size="small" onClick={() => {
                form.setFieldsValue({
                  name: p.key, provider_type: p.key, base_url: p.base_url,
                  default_model: p.default_model, input_price: p.input_price,
                  output_price: p.output_price, models_list: p.models,
                });
                setModalOpen(true);
              }}>{p.name}</Button>
            ))}
          </Space>
        </div>
      )}

      <Table dataSource={providers} columns={columns} rowKey="id" loading={loading} size="small" pagination={false} />

      <Modal title="新建 Model Provider" open={modalOpen} onCancel={() => setModalOpen(false)} onOk={() => form.submit()}>
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Form.Item name="name" label="名称" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="provider_type" label="类型" initialValue="openai_compatible">
            <Select options={[
              { value: "deepseek", label: "DeepSeek" }, { value: "zhipu", label: "智谱 GLM" },
              { value: "qwen", label: "通义千问" }, { value: "openai_compatible", label: "OpenAI 兼容" },
            ]} />
          </Form.Item>
          <Form.Item name="base_url" label="Base URL"><Input /></Form.Item>
          <Form.Item name="api_key_encrypted" label="API Key"><Input.Password /></Form.Item>
          <Form.Item name="default_model" label="默认模型"><Input /></Form.Item>
        </Form>
      </Modal>
    </div>
  );
}

// ── Action Tab ────────────────────────────────────────────────

function ActionTab() {
  const [actions, setActions] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const loadActions = async () => {
    setLoading(true);
    try { const r = await aiopsApi.getActions(); setActions(r.data.actions || []); } catch {}
    setLoading(false);
  };
  useEffect(() => { loadActions(); }, []);

  const columns = [
    { title: "Code", dataIndex: "code", key: "code" },
    { title: "显示名", dataIndex: "display_name", key: "name" },
    { title: "模式", dataIndex: "agent_mode_display", key: "mode", render: (v: string) => <Tag>{v}</Tag> },
    { title: "风险", dataIndex: "risk_level_display", key: "risk", render: (v: string) => <Tag color={v === "只读" ? "green" : "orange"}>{v}</Tag> },
    { title: "匹配路由", dataIndex: "page_prefixes", key: "routes", render: (v: string[]) => v?.join(", ") },
    { title: "关键词", dataIndex: "keywords", key: "keywords", render: (v: string[]) => v?.slice(0, 3).join(", "), ellipsis: true },
    { title: "默认工具", dataIndex: "enabled_tools", key: "tools", render: (v: string[]) => v?.join(", "), ellipsis: true },
  ];

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Button icon={<ReloadOutlined />} onClick={loadActions}>刷新</Button>
      </Space>
      <Table dataSource={actions} columns={columns} rowKey="code" loading={loading} size="small" pagination={false} />
    </div>
  );
}
