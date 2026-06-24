import { useCallback } from "react";
import { useQuery } from "@tanstack/react-query";
import { Card, Spin, Tag, Typography, Row, Col } from "antd";
import ReactFlow, { Background, Controls, Handle, Position, Node, Edge } from "reactflow";
import "reactflow/dist/style.css";
import client from "../../api/client";

const { Text } = Typography;

const healthColor: Record<string, string> = { healthy: "#52c41a", warning: "#fa8c16", critical: "#f5222d" };
const typeStyle: Record<string, { bg: string; border: string; width: number }> = {
  service: { bg: "#e6f4ff", border: "#1677ff", width: 160 },
  database: { bg: "#fff7e6", border: "#fa8c16", width: 150 },
  cache: { bg: "#f6ffed", border: "#52c41a", width: 130 },
  queue: { bg: "#f9f0ff", border: "#722ed1", width: 140 },
  host: { bg: "#fafafa", border: "#8c8c8c", width: 140 },
  switch: { bg: "#fff2e8", border: "#d46b08", width: 140 },
};

function CustomNode({ data }: any) {
  const style = typeStyle[data.nodeType] || typeStyle.service;
  return (
    <div style={{ background: style.bg, border: `2px solid ${style.border}`, borderRadius: 12, padding: "12px 16px", width: style.width, textAlign: "center", boxShadow: "0 2px 8px rgba(0,0,0,0.08)" }}>
      <Handle type="target" position={Position.Top} />
      <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 4 }}>{data.label}</div>
      <Tag color={healthColor[data.health]} style={{ margin: 0, fontSize: 11 }}>{data.health === "healthy" ? "健康" : data.health === "warning" ? "警告" : "异常"}</Tag>
      {data.metrics && <div style={{ marginTop: 4, fontSize: 11, color: "#8c8c8c" }}>{data.metrics}</div>}
      <Handle type="source" position={Position.Bottom} />
    </div>
  );
}

const nodeTypes = { custom: CustomNode };

export default function TopologyPage() {
  const { data: topo, isLoading } = useQuery({ queryKey: ["topology"], queryFn: () => client.get("/apm/topology").then((r) => r.data) });

  const buildGraph = useCallback(() => {
    if (!topo) return { nodes: [], edges: [] };
    const nodeMap: Record<string, any> = {};
    topo.nodes.forEach((n: any) => { nodeMap[n.id] = n; });

    const layerY: Record<string, number> = { application: 50, infrastructure: 280, network: 490 };
    const layerOrder: Record<string, string[]> = { application: [], infrastructure: [], network: [] };
    topo.nodes.forEach((n: any) => { layerOrder[n.layer]?.push(n.id); });

    const nodes: Node[] = [];
    const edges: Edge[] = [];
    const layerWidth = 800;

    Object.entries(layerOrder).forEach(([layer, ids]) => {
      ids.forEach((id, i) => {
        const n = nodeMap[id];
        const x = i * 180 + 50;
        nodes.push({
          id: n.id,
          type: "custom",
          position: { x, y: layerY[layer] || 200 },
          data: { label: n.label, nodeType: n.type, health: n.health, metrics: n.metrics },
        });
      });
    });

    topo.edges.forEach((e: any) => {
      edges.push({
        id: `${e.source}-${e.target}`,
        source: e.source,
        target: e.target,
        animated: e.status === "critical",
        style: { stroke: e.status === "critical" ? "#f5222d" : e.status === "warning" ? "#fa8c16" : "#1890ff", strokeWidth: e.status === "critical" ? 3 : 1.5 },
        label: e.latency_ms ? `${e.latency_ms}ms` : "",
        labelStyle: { fontSize: 10, fill: e.status === "critical" ? "#f5222d" : "#8c8c8c" },
      });
    });

    return { nodes, edges };
  }, [topo]);

  const bg = "🎨 三层拓扑: 应用层(服务) → 基础设施层(主机) → 网络层(交换机)";

  if (isLoading) return <Spin size="large" style={{ display: "block", margin: "200px auto" }} />;

  return (
    <div>
      <Card title="服务依赖拓扑 (F6.4 + F6.5)" extra={<Text type="secondary">{bg}</Text>} style={{ marginBottom: 16 }}>
        <div style={{ height: 580, border: "1px solid #f0f0f0", borderRadius: 8, background: "#fafbfc" }}>
          <ReactFlow nodes={buildGraph().nodes} edges={buildGraph().edges} nodeTypes={nodeTypes} fitView>
            <Background color="#f0f0f0" gap={20} />
            <Controls />
          </ReactFlow>
        </div>
      </Card>
      <Row gutter={16}>
        <Col span={8}>
          <Card size="small" title="图例">
            <div style={{ display: "flex", gap: 16, flexWrap: "wrap" }}>
              {Object.entries(typeStyle).map(([k, v]) => <Tag key={k} color={v.border}>{k}</Tag>)}
            </div>
            <div style={{ marginTop: 8, display: "flex", gap: 8 }}>
              <Tag color="green">健康</Tag><Tag color="orange">警告</Tag><Tag color="red">异常</Tag>
            </div>
          </Card>
        </Col>
        <Col span={16}>
          <Card size="small" title="当前跨层定界状态">
            <Text>支付服务 (payment-service) → MySQL (mysql-db) 链路异常，</Text>
            <Text type="danger">P99 延迟 3500ms</Text>
            <Text>。AI 跨层定界 (H8.10): </Text>
            <Text strong>75% 数据库层 → 20% 网络层 → 5% 应用代码层</Text>
          </Card>
        </Col>
      </Row>
    </div>
  );
}
