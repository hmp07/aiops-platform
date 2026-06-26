import { useState, useRef, useEffect } from "react";
import { Card, Input, Button, Space, Typography, Tag, Spin, List, message, Divider } from "antd";
import { SendOutlined, RobotOutlined, UserOutlined, ThunderboltOutlined, DeleteOutlined, PlusOutlined } from "@ant-design/icons";
import ReactMarkdown from "react-markdown";
import client from "../../api/client";

const { Text, Title } = Typography;

interface Message { role: "user" | "ai"; content: string; cardType?: string; }
interface Session { id: string; title: string; message_count: number; }

const suggestions = [
  "支付服务最近1小时有异常吗？", "CORE-SW-01的CPU为什么这么高？",
  "最近有哪些配置变更？", "数据库慢查询影响了哪些业务？",
  "当前网络拓扑健康状态怎么样？",
];

export default function AIChatPage() {
  const [messages, setMessages] = useState<Message[]>([{
    role: "ai",
    content: "您好！我是 AIOps 智能运维助手。我可以帮您分析告警根因、查询设备状态、评估变更风险。请尝试以下问题或直接输入：",
  }]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  useEffect(() => {
    client.get("/ai/sessions").then(r => setSessions(r.data.items || [])).catch(() => {});
  }, []);

  const createSession = async () => {
    try {
      const r = await client.post("/ai/sessions", { title: "New Chat" });
      setSessions(prev => [r.data, ...prev]);
      setActiveSessionId(r.data.id);
      setMessages([{ role: "ai", content: "新会话已创建。请提出您的运维问题。" }]);
    } catch { message.error("创建会话失败"); }
  };

  const handleSend = async (text?: string) => {
    const q = text || input;
    if (!q.trim() || loading) return;
    let sid = activeSessionId;
    if (!sid) {
      try {
        const r = await client.post("/ai/sessions", { title: q.slice(0, 50) });
        sid = r.data.id;
        setActiveSessionId(sid);
      } catch { message.error("创建会话失败"); return; }
    }

    setMessages(prev => [...prev, { role: "user", content: q }]);
    setInput("");
    setLoading(true);

    const token = localStorage.getItem("access_token") || "";
    try {
      const resp = await fetch(`/api/v1/ai/sessions/${sid}/messages`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ content: q }),
      });
      const reader = resp.body?.getReader();
      const decoder = new TextDecoder();
      let aiContent = "";
      setMessages(prev => [...prev, { role: "ai", content: "" }]);

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          const chunk = decoder.decode(value, { stream: true });
          const lines = chunk.split("\n");
          for (const line of lines) {
            if (!line.startsWith("data: ")) continue;
            const data = line.slice(6).trim();
            if (!data || data === "[DONE]") continue;
            try {
              const parsed = JSON.parse(data);
              // rich_card has the final formatted answer
              if (parsed.card_type === "text_response") {
                aiContent = parsed.data?.text || "";
              } else if (parsed.content) {
                // thought events show reasoning steps
                aiContent += (aiContent ? "\n" : "") + "_" + parsed.content + "_";
              }
              setMessages(prev => {
                const copy = [...prev];
                copy[copy.length - 1] = { role: "ai", content: aiContent };
                return copy;
              });
            } catch {}
          }
        }
      }
    } catch {
      setMessages(prev => [...prev, { role: "ai", content: "AI 服务暂时不可用，请稍后再试。" }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: "flex", gap: 16, height: "calc(100vh - 140px)" }}>
      {/* Session Sidebar */}
      <Card size="small" style={{ width: 220, overflow: "auto" }} title={
        <Space><Button type="primary" size="small" icon={<PlusOutlined />} onClick={createSession}>新建</Button></Space>
      }>
        <List dataSource={sessions} renderItem={(s: Session) => (
          <List.Item onClick={async () => { setActiveSessionId(s.id); setMessages([{ role: "ai", content: "加载中..." }]); try { const r = await client.get(`/ai/sessions/${s.id}/messages`); const msgs = (r.data.items || []).map((m: any) => ({ role: m.role === "assistant" ? "ai" as const : "user" as const, content: m.content || "" })); setMessages([{ role: "ai" as const, content: "会话已加载。" }, ...msgs]); } catch { setMessages([{ role: "ai", content: "加载失败" }]); } }} style={{ cursor: "pointer", background: activeSessionId === s.id ? "#e6f4ff" : undefined }}>
            <Text ellipsis style={{ fontSize: 13 }}>{s.title}</Text>
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
                {m.role === "ai" ? <ReactMarkdown>{m.content}</ReactMarkdown> : <Text style={{ color: "#fff" }}>{m.content}</Text>}
              </div>
              {m.role === "user" && <UserOutlined style={{ fontSize: 18, color: "#1677ff", marginTop: 4 }} />}
            </div>
          ))}
          {loading && <Spin tip="AI 分析中..." />}
          <div ref={bottomRef} />
        </div>

        <div style={{ marginBottom: 8 }}>
          {suggestions.map(s => <Tag key={s} color="blue" style={{ cursor: "pointer", marginBottom: 4 }} onClick={() => handleSend(s)}>{s}</Tag>)}
        </div>

        <Space.Compact style={{ width: "100%" }}>
          <Input.TextArea value={input} onChange={e => setInput(e.target.value)}
            onPressEnter={e => { e.preventDefault(); handleSend(); }}
            placeholder="输入运维问题..." autoSize={{ minRows: 1, maxRows: 4 }} disabled={loading} />
          <Button type="primary" icon={<SendOutlined />} onClick={() => handleSend()} loading={loading}>发送</Button>
        </Space.Compact>
      </Card>
    </div>
  );
}
