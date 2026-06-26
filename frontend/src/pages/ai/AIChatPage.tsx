import { useState, useRef, useEffect, useCallback } from "react";
import { Card, Input, Button, Space, Typography, Tag, Spin, List, message, Popconfirm } from "antd";
import { SendOutlined, RobotOutlined, UserOutlined, PlusOutlined, DeleteOutlined, LoadingOutlined, CheckCircleOutlined } from "@ant-design/icons";
import ReactMarkdown from "react-markdown";
import client from "../../api/client";

const { Text } = Typography;

interface Message {
  id?: string; role: "user" | "ai"; content: string;
  processing_status?: string; blocks?: any; citations?: any;
}
interface Session { id: string; title: string; message_count: number; }

export default function AIChatPage() {
  const [messages, setMessages] = useState<Message[]>([{
    role: "ai", content: "您好！我是 AIOps 智能运维助手。请提出您的运维问题。",
  }]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);
  useEffect(() => { loadSessions(); }, []);
  useEffect(() => () => { if (pollingRef.current) clearInterval(pollingRef.current); }, []);

  const loadSessions = async () => {
    try { const r = await client.get("/aiops/sessions"); setSessions(r.data.items || []); } catch {}
  };

  const createSession = async () => {
    try {
      const r = await client.post("/aiops/sessions", { title: "New Chat" });
      setSessions(prev => [r.data, ...prev]);
      selectSession(r.data.id);
    } catch { message.error("创建会话失败"); }
  };

  const selectSession = async (sid: string) => {
    stopPolling();
    setActiveSessionId(sid);
    try {
      const r = await client.get(`/aiops/sessions/${sid}/messages`);
      const msgs = (r.data.items || []).map((m: any) => ({
        id: m.id, role: m.role === "assistant" ? "ai" as const : "user" as const,
        content: m.content || "", processing_status: m.processing_status,
        blocks: m.blocks, citations: m.citations,
      }));
      setMessages(msgs.length > 0 ? msgs : [{ role: "ai", content: "会话已加载。" }]);
    } catch { setMessages([{ role: "ai", content: "加载失败" }]); }
  };

  const deleteSession = async (sid: string) => {
    try {
      await client.post(`/aiops/sessions/${sid}/delete_session`);
      setSessions(prev => prev.filter(s => s.id !== sid));
      if (activeSessionId === sid) { setActiveSessionId(null); setMessages([{ role: "ai", content: "会话已删除。请新建会话。" }]); }
    } catch { message.error("删除失败"); }
  };

  const stopPolling = () => {
    if (pollingRef.current) { clearInterval(pollingRef.current); pollingRef.current = null; }
  };

  const startPolling = (sid: string, msgId: string) => {
    stopPolling();
    let attempts = 0;
    pollingRef.current = setInterval(async () => {
      attempts++;
      try {
        const r = await client.get(`/aiops/sessions/${sid}/messages`);
        const items: any[] = r.data.items || [];
        const msgs = items.map((m: any) => ({
          id: m.id, role: m.role === "assistant" ? "ai" as const : "user" as const,
          content: m.content || "", processing_status: m.processing_status,
        }));
        setMessages(msgs);
        const last = items[items.length - 1];
        if (last && last.role === "assistant" && last.processing_status !== "pending" && last.processing_status !== "running") {
          stopPolling();
          setSending(false);
          loadSessions();
        }
        if (attempts > 60) { stopPolling(); setSending(false); }
      } catch { stopPolling(); setSending(false); }
    }, 1500);
  };

  const handleSend = useCallback(async (text?: string) => {
    const q = (text || input).trim();
    if (!q || sending) return;
    let sid: string = activeSessionId || "";
    if (!sid) {
      try { const r = await client.post("/aiops/sessions", { title: q.slice(0, 50) }); sid = r.data.id; setActiveSessionId(sid); setSessions(prev => [r.data, ...prev]); }
      catch { message.error("创建会话失败"); return; }
    }
    if (!sid) return;
    setMessages(prev => [...prev, { role: "user", content: q }, { role: "ai", content: "", processing_status: "pending" }]);
    setInput(""); setSending(true);

    try {
      await client.post(`/aiops/sessions/${sid}/send_message_async`, { content: q });
      // Trigger execution (blocks until done)
      client.post(`/aiops/sessions/${sid}/execute_pending`, {}, { timeout: 60000 }).catch(() => {});
      // Start polling
      startPolling(sid, "");
    } catch { setSending(false); message.error("发送失败"); }
  }, [input, activeSessionId, sending]);

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
        <div style={{ flex: 1, overflow: "auto", marginBottom: 12 }}>
          {messages.map((m, i) => (
            <div key={i} style={{ marginBottom: 12, display: "flex", gap: 10, justifyContent: m.role === "user" ? "flex-end" : "flex-start" }}>
              {m.role === "ai" && <RobotOutlined style={{ fontSize: 18, color: "#1677ff", marginTop: 4 }} />}
              <div style={{ maxWidth: "80%", padding: "10px 14px", borderRadius: 10, background: m.role === "user" ? "#1677ff" : "#f5f5f5", color: m.role === "user" ? "#fff" : "inherit" }}>
                {m.processing_status === "pending" || m.processing_status === "running" ? (
                  <Space><LoadingOutlined /><Text type="secondary">AI 分析中...</Text></Space>
                ) : m.role === "ai" ? (
                  m.content ? <ReactMarkdown>{m.content}</ReactMarkdown> : <Text type="secondary">...</Text>
                ) : (
                  <Text style={{ color: "#fff" }}>{m.content}</Text>
                )}
              </div>
              {m.role === "user" && <UserOutlined style={{ fontSize: 18, color: "#1677ff", marginTop: 4 }} />}
            </div>
          ))}
          <div ref={bottomRef} />
        </div>

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
