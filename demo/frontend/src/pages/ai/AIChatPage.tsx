import { useState, useRef, useEffect } from "react";
import { Card, Input, Button, Space, Typography, Tag, Spin, Alert } from "antd";
import { SendOutlined, RobotOutlined, UserOutlined, ThunderboltOutlined } from "@ant-design/icons";
import ReactMarkdown from "react-markdown";
import client from "../../api/client";

const { Text, Title } = Typography;

interface Message { role: "user" | "ai"; content: string; }

const suggestions = [
  "支付服务最近1小时有异常吗？",
  "CORE-SW-01的CPU为什么这么高？",
  "最近有哪些配置变更？",
  "数据库慢查询影响了哪些业务？",
  "当前网络拓扑健康状态怎么样？",
];

export default function AIChatPage() {
  const [messages, setMessages] = useState<Message[]>([{ role: "ai", content: "你好！我是 AIOps 智能运维助手。我可以帮你分析告警根因、查询设备状态、评估变更风险、回答运维问题。请尝试以下问题或直接输入你的问题：" }]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  const handleSend = async (text?: string) => {
    const q = text || input;
    if (!q.trim() || loading) return;
    const userMsg: Message = { role: "user", content: q };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const response = await fetch("/api/v1/ai/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: q }),
      });
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let aiContent = "";
      setMessages((prev) => [...prev, { role: "ai", content: "" }]);

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          const chunk = decoder.decode(value);
          const lines = chunk.split("\n").filter((l) => l.startsWith("data: "));
          for (const line of lines) {
            const data = line.slice(6);
            if (data === "[DONE]") break;
            try {
              const parsed = JSON.parse(data);
              aiContent += parsed.content;
              setMessages((prev) => {
                const copy = [...prev];
                copy[copy.length - 1] = { role: "ai", content: aiContent };
                return copy;
              });
            } catch {}
          }
        }
      }
    } catch {
      setMessages((prev) => [...prev, { role: "ai", content: "抱歉，AI 服务暂时不可用，请稍后再试。" }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 900, margin: "0 auto" }}>
      <Card title={<Space><RobotOutlined style={{ color: "#1677ff" }} /><Title level={5} style={{ margin: 0 }}>AI 智能运维问答 (H8.9)</Title></Space>} extra={<Tag icon={<ThunderboltOutlined />} color="blue">ReAct Agent</Tag>}>
        <div style={{ height: 480, overflowY: "auto", marginBottom: 16, padding: "0 8px" }}>
          {messages.map((m, i) => (
            <div key={i} style={{ marginBottom: 16, display: "flex", gap: 12, justifyContent: m.role === "user" ? "flex-end" : "flex-start" }}>
              {m.role === "ai" && <RobotOutlined style={{ fontSize: 20, color: "#1677ff", marginTop: 4 }} />}
              <div style={{ maxWidth: "80%", padding: "12px 16px", borderRadius: 12, background: m.role === "user" ? "#1677ff" : "#f5f5f5", color: m.role === "user" ? "#fff" : "inherit" }}>
                {m.role === "ai" ? <ReactMarkdown>{m.content}</ReactMarkdown> : <Text style={{ color: "#fff" }}>{m.content}</Text>}
              </div>
              {m.role === "user" && <UserOutlined style={{ fontSize: 20, color: "#1677ff", marginTop: 4 }} />}
            </div>
          ))}
          {loading && <Spin tip="AI 分析中..." />}
          <div ref={bottomRef} />
        </div>

        <div style={{ marginBottom: 12 }}>
          <Text type="secondary">建议问题：</Text>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginTop: 4 }}>
            {suggestions.map((s) => (
              <Tag key={s} style={{ cursor: "pointer" }} color="blue" onClick={() => handleSend(s)}>{s}</Tag>
            ))}
          </div>
        </div>

        <Space.Compact style={{ width: "100%" }}>
          <Input.TextArea value={input} onChange={(e) => setInput(e.target.value)} onPressEnter={(e) => { e.preventDefault(); handleSend(); }} placeholder="输入你的运维问题..." autoSize={{ minRows: 1, maxRows: 4 }} disabled={loading} />
          <Button type="primary" icon={<SendOutlined />} onClick={() => handleSend()} loading={loading}>发送</Button>
        </Space.Compact>
      </Card>

      <Alert type="info" style={{ marginTop: 16 }} message={
        <div>
          <Text strong>Demo 说明：</Text>
          <Text>点击上方建议问题即可体验 AI 问答能力。AI 响应基于 ReAct Agent 架构（推理→工具调用→观察→结论），所有回答均由模拟数据生成，实际部署后将接入真实 LLM 和多模块数据源。</Text>
        </div>
      } />
    </div>
  );
}
