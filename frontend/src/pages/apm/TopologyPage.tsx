import { useQuery } from "@tanstack/react-query";
import { Card, Spin, Tag, Empty } from "antd";
import ReactFlow, { Background, Controls, Handle, Position } from "reactflow";
import "reactflow/dist/style.css";
import { apmApi } from "../../api/modules";

const healthColor: Record<string, string> = { healthy: "#52c41a", warning: "#fa8c16", critical: "#f5222d" };

function CustomNode({ data }: any) {
  return (
    <div style={{ background: "#e6f4ff", border: "2px solid #1677ff", borderRadius: 12, padding: "10px 14px", textAlign: "center" }}>
      <Handle type="target" position={Position.Top} />
      <div style={{ fontWeight: 600, fontSize: 13 }}>{data.label}</div>
      <Tag color={healthColor[data.health]} style={{ fontSize: 11 }}>{data.health}</Tag>
      <Handle type="source" position={Position.Bottom} />
    </div>
  );
}

export default function TopologyPage() {
  const { data, isLoading } = useQuery({ queryKey: ["topology"], queryFn: () => apmApi.getTopology().then(r => r.data) });
  if (isLoading) return <Spin size="large" style={{ display: "block", margin: "200px auto" }} />;
  if (!data?.nodes?.length) return <Empty description="No topology data. Add services and edges first." />;

  const nodes = data.nodes.map((n: any, i: number) => ({
    id: n.id, type: "custom",
    position: { x: (i % 4) * 200 + 50, y: Math.floor(i / 4) * 150 + 50 },
    data: { label: n.label, health: n.health },
  }));
  const edges = (data.edges || []).map((e: any) => ({
    id: e.source + "-" + e.target, source: e.source, target: e.target,
    animated: e.status === "critical",
    style: { stroke: e.status === "critical" ? "#f5222d" : "#1890ff", strokeWidth: 1.5 },
  }));

  return (
    <Card title="Service Topology">
      <div style={{ height: 500, border: "1px solid #f0f0f0", borderRadius: 8 }}>
        <ReactFlow nodes={nodes} edges={edges} nodeTypes={{ custom: CustomNode }} fitView>
          <Background color="#f0f0f0" gap={20} /><Controls />
        </ReactFlow>
      </div>
    </Card>
  );
}
