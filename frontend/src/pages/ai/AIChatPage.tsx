import { useState, useRef, useEffect, useCallback } from "react";
import {
  Card, Input, Button, Space, Typography, Tag, List, message, Popconfirm,
  Collapse, Badge, Switch,
} from "antd";
import {
  SendOutlined, RobotOutlined, UserOutlined, PlusOutlined, DeleteOutlined,
  LoadingOutlined, CheckCircleOutlined, CloseCircleOutlined,
  ToolOutlined, QuestionCircleOutlined,
} from "@ant-design/icons";
import ReactMarkdown from "react-markdown";
import * as aiopsApi from "../../api/aiops";

const { Text } = Typography;

interface Message {
  id?: string; role: "user" | "ai"; content: string;
  processing_status?: string; blocks?: any; citations?: any;
  metadata?: any; pending_action_id?: string;
}
interface Session { id: string; title: string; message_count: number; }
interface BootstrapData {
  enabled: boolean; welcome_message: string; suggested_questions: string[];
  permissions: any; provider: any; runtime: any;
}

export default function AIChatPage() {
  const [messages, setMessages] = useState<Message[]>([{
    role: "ai", content: "您好！我是 AIOps 智能运维助手。请提出您的运维问题。",
  }]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [bootstrap, setBootstrap] = useState<BootstrapData | null>(null);
  const [analysisOnly, setAnalysisOnly] = useState(true);
  const [expandedProcess, setExpandedProcess] = useState<Set<string>>(new Set());
  const bottomRef = useRef<HTMLDivElement>(null);
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);
  useEffect(() => { loadBootstrap(); loadSessions(); }, []);
  useEffect(() => () => { if (pollingRef.current) clearInterval(pollingRef.current); }, []);

  const loadBootstrap = async () => {
    try { const r = await aiopsApi.getBootstrap(); setBootstrap(r.data); } catch {}
  };

  const loadSessions = async () => {
    try { const r = await aiopsApi.getSessions(); setSessions(r.data.items || []); } catch {}
  };

  const createSession = async () => {
    try {
      const r = await aiopsApi.createSession({ title: "New Chat" });
      setSessions(prev => [r.data, ...prev]);
      selectSession(r.data.id);
    } catch { message.error("创建会话失败"); }
  };

  const selectSession = async (sid: string) => {
    stopPolling();
    setActiveSessionId(sid);
    try {
      const r = await aiopsApi.getMessages(sid);
      const msgs = (r.data.items || []).map((m: any) => ({
        id: m.id, role: m.role === "assistant" ? "ai" as const : "user" as const,
        content: m.content || "", processing_status: m.processing_status,
        blocks: m.blocks, citations: m.citations, metadata: m.metadata,
        pending_action_id: m.pending_action_id,
      }));
      setMessages(msgs.length > 0 ? msgs : [{ role: "ai", content: "会话已加载。" }]);
    } catch { setMessages([{ role: "ai", content: "加载失败" }]); }
  };

  const deleteSession = async (sid: string) => {
    try {
      await aiopsApi.deleteSession(sid);
      setSessions(prev => prev.filter(s => s.id !== sid));
      if (activeSessionId === sid) { setActiveSessionId(null); setMessages([{ role: "ai", content: "会话已删除。请新建会话。" }]); }
    } catch { message.error("删除失败"); }
  };

  const stopPolling = () => {
    if (pollingRef.current) { clearInterval(pollingRef.current); pollingRef.current = null; }
  };

  const startPolling = (sid: string) => {
    stopPolling();
    let attempts = 0;
    pollingRef.current = setInterval(async () => {
      attempts++;
      try {
        const r = await aiopsApi.getMessages(sid);
        const items: any[] = r.data.items || [];
        const msgs = items.map((m: any) => ({
          id: m.id, role: m.role === "assistant" ? "ai" as const : "user" as const,
          content: m.content || "", processing_status: m.processing_status,
          blocks: m.blocks, citations: m.citations, metadata: m.metadata,
          pending_action_id: m.pending_action_id,
        }));
        setMessages(msgs);
        const last = items[items.length - 1];
        if (last && last.role === "assistant" && last.processing_status !== "pending" && last.processing_status !== "running") {
          stopPolling(); setSending(false); loadSessions();
        }
        if (attempts > 90) { stopPolling(); setSending(false); }
      } catch { stopPolling(); setSending(false); }
    }, 1500);
  };

  const handleSend = useCallback(async (text?: string) => {
    const q = (text || input).trim();
    if (!q || sending) return;
    let sid: string | null = activeSessionId;
    if (!sid) {
      try { const r = await aiopsApi.createSession({ title: q.slice(0, 50) }); sid = r.data.id; setActiveSessionId(sid); setSessions(prev => [r.data, ...prev]); }
      catch { message.error("创建会话失败"); return; }
    }
    if (!sid) return;
    setMessages(prev => [...prev, { role: "user", content: q }, { role: "ai", content: "", processing_status: "pending" }]);
    setInput(""); setSending(true);

    try {
      await aiopsApi.sendMessageAsync(sid, { content: q, context: { analysis_only: analysisOnly } });
      aiopsApi.executePending(sid).catch(() => {});
      startPolling(sid);
    } catch { setSending(false); message.error("发送失败"); }
  }, [input, activeSessionId, sending, analysisOnly]);

  const toggleProcess = (msgKey: string) => {
    setExpandedProcess(prev => {
      const next = new Set(prev);
      next.has(msgKey) ? next.delete(msgKey) : next.add(msgKey);
      return next;
    });
  };

  const getProcessSummary = (m: Message) => {
    const steps = m.metadata?.processing_steps || m.metadata?.tool_events || [];
    if (!steps.length) return m.processing_status === "running" ? "分析中..." : "";
    return steps.map((s: any) => s.title || s.name || "").join(" → ");
  };

  const isProcessing = (m: Message) =>
    m.processing_status === "pending" || m.processing_status === "running";

  const renderMessageContent = (m: Message, i: number) => {
    const msgKey = m.id || String(i);

    if (m.role === "user") {
      return <Text style={{ color: "#fff" }}>{m.content}</Text>;
    }

    if (isProcessing(m)) {
      return (
        <Space direction="vertical" size={4} style={{ width: "100%" }}>
          <Space><LoadingOutlined spin /><Text type="secondary">{getProcessSummary(m) || "AI 分析中..."}</Text></Space>
          {m.metadata?.processing_steps && m.metadata.processing_steps.length > 0 && (
            <Collapse ghost size="small" items={[{
              key: "steps", label: <Text type="secondary" style={{ fontSize: 12 }}>思考过程</Text>,
              children: <div style={{ fontSize: 12 }}>
                {m.metadata.processing_steps.map((s: any, si: number) => (
                  <div key={si} style={{ color: s.status === "failed" ? "#ff4d4f" : "#666" }}>
                    {s.status === "completed" ? <CheckCircleOutlined style={{ color: "#52c41a", marginRight: 4 }} /> :
                     s.status === "running" ? <LoadingOutlined style={{ marginRight: 4 }} /> :
                     <CloseCircleOutlined style={{ color: "#ff4d4f", marginRight: 4 }} />}
                    {s.title}
                  </div>
                ))}
              </div>
            }]} />
          )}
        </Space>
      );
    }

    // Show tool events card for completed messages
    if (m.metadata?.tool_events && m.metadata.tool_events.length > 0) {
      const expanded = expandedProcess.has(msgKey);
      return (
        <div>
          <Collapse
            ghost size="small"
            activeKey={expanded ? ["process"] : []}
            onChange={() => toggleProcess(msgKey)}
            items={[{
              key: "process",
              label: (
                <Space size={4}>
                  <Badge status="success" />
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    <ToolOutlined /> {m.metadata.tool_events.map((t: any) => t.name).join(", ")}
                    {" — "}{m.metadata.tool_events.map((t: any) => t.detail).join("; ")}
                  </Text>
                </Space>
              ),
              children: (
                <div style={{ fontSize: 12, paddingLeft: 16 }}>
                  {(m.metadata?.processing_steps || []).map((s: any, si: number) => (
                    <div key={si}>
                      <CheckCircleOutlined style={{ color: "#52c41a", marginRight: 4 }} />{s.title}
                    </div>
                  ))}
                </div>
              ),
            }]}
          />
          <div style={{ marginTop: 8 }}>
            {m.content ? <ReactMarkdown>{m.content}</ReactMarkdown> : <Text type="secondary">...</Text>}
          </div>
        </div>
      );
    }

    if (m.content) return <ReactMarkdown>{m.content}</ReactMarkdown>;
    return <Text type="secondary">...</Text>;
  };

  return (
    <div style={{ display: "flex", gap: 16, height: "calc(100vh - 140px)" }}>
      {/* Session Sidebar */}
      <Card size="small" style={{ width: 220, overflow: "auto" }} title={
        <Button type="primary" size="small" icon={<PlusOutlined />} onClick={createSession} block>新建会话</Button>
      }>
        <List dataSource={sessions} locale={{ emptyText: "暂无会话" }} renderItem={(s: Session) => (
          <List.Item
            onClick={() => selectSession(s.id!)}
            style={{ cursor: "pointer", background: activeSessionId === s.id ? "#e6f4ff" : undefined, padding: "6px 8px", borderRadius: 6 }}
            actions={[<Popconfirm key="del" title="删除?" onConfirm={() => deleteSession(s.id)}><DeleteOutlined style={{ fontSize: 12, color: "#999" }} /></Popconfirm>]}
          >
            <Text ellipsis style={{ fontSize: 13, flex: 1 }}>{s.title || "New Chat"}</Text>
          </List.Item>
        )} />
      </Card>

      {/* Chat Area */}
      <Card style={{ flex: 1, display: "flex", flexDirection: "column" }} bodyStyle={{ flex: 1, display: "flex", flexDirection: "column", padding: 12 }}>
        {/* Toolbar */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8, paddingBottom: 8, borderBottom: "1px solid #f0f0f0" }}>
          <Space size={12}>
            <Text strong style={{ fontSize: 13 }}>
              {sessions.find(s => s.id === activeSessionId)?.title || "新会话"}
            </Text>
            {bootstrap?.provider && (
              <Tag color="blue" style={{ fontSize: 11 }}>{bootstrap.provider.name} / {bootstrap.provider.model}</Tag>
            )}
          </Space>
          <Space size={8}>
            <Text type="secondary" style={{ fontSize: 12 }}>只分析模式</Text>
            <Switch size="small" checked={analysisOnly} onChange={setAnalysisOnly} />
          </Space>
        </div>

        {/* Quick Questions */}
        {!messages.some(m => m.role === "user") && bootstrap?.suggested_questions && (
          <div style={{ marginBottom: 12, display: "flex", flexWrap: "wrap", gap: 6 }}>
            {bootstrap.suggested_questions.slice(0, 6).map((q, i) => (
              <Button key={i} size="small" type="default" icon={<QuestionCircleOutlined />}
                onClick={() => handleSend(q)} style={{ borderRadius: 16, fontSize: 12 }}>
                {q.length > 30 ? q.slice(0, 30) + "..." : q}
              </Button>
            ))}
          </div>
        )}

        {/* Messages */}
        <div style={{ flex: 1, overflow: "auto", marginBottom: 12 }}>
          {messages.map((m, i) => (
            <div key={i} style={{ marginBottom: 12, display: "flex", gap: 10, justifyContent: m.role === "user" ? "flex-end" : "flex-start" }}>
              {m.role === "ai" && <RobotOutlined style={{ fontSize: 18, color: "#1677ff", marginTop: 4 }} />}
              <div style={{
                maxWidth: "85%", padding: "10px 14px", borderRadius: 10,
                background: m.role === "user" ? "#1677ff" : "#f5f5f5",
                color: m.role === "user" ? "#fff" : "inherit",
              }}>
                {renderMessageContent(m, i)}
              </div>
              {m.role === "user" && <UserOutlined style={{ fontSize: 18, color: "#1677ff", marginTop: 4 }} />}
            </div>
          ))}
          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <Space.Compact style={{ width: "100%" }}>
          <Input.TextArea value={input} onChange={e => setInput(e.target.value)}
            onPressEnter={e => { e.preventDefault(); handleSend(); }}
            placeholder="输入运维问题..." autoSize={{ minRows: 1, maxRows: 4 }} disabled={sending} />
          <Button type="primary" icon={<SendOutlined />} onClick={() => handleSend()} loading={sending}>发送</Button>
        </Space.Compact>
      </Card>
    </div>
  );
}
