import { useState, useCallback, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { Spin, Empty, Select, Button, Space, Tag, message, Typography, Tooltip } from "antd";
import { ReloadOutlined, NodeIndexOutlined, AimOutlined } from "@ant-design/icons";
import ReactFlow, { Background, Controls, Handle, Position, MarkerType, useReactFlow } from "reactflow";
import "reactflow/dist/style.css";
import dagre from "dagre";
import { apmApi } from "../../api/modules";

const { Text } = Typography;

// ── dagre layout engine (top-down hierarchical) ──
function layoutDagre(nodes: any[], edges: any[]) {
  const g = new dagre.graphlib.Graph();
  g.setDefaultEdgeLabel(() => ({}));
  g.setGraph({ rankdir: "TB", ranksep: 80, nodesep: 60, marginx: 40, marginy: 40 });

  nodes.forEach(n => g.setNode(n.id, { width: 150, height: 60 }));
  edges.forEach(e => g.setEdge(e.source, e.target));

  dagre.layout(g);

  return nodes.map(n => {
    const pos = g.node(n.id);
    return { ...n, position: { x: pos.x - 75, y: pos.y - 30 } };
  });
}

// ── node type → color map ──
const typeColor: Record<string, string> = {
  ApplicationSolution: "#1677ff",
  DatabaseSchema: "#722ed1",
  DBServer: "#531dab",
  WebServer: "#13c2c2",
  WebApplication: "#08979c",
  VirtualMachine: "#52c41a",
  Farm: "#237804",
  Hypervisor: "#fa8c16",
  Server: "#d4380d",
  NetworkDevice: "#faad14",
  StorageSystem: "#eb2f96",
  Rack: "#8c8c8c",
};

// ── custom ReactFlow node for iTop CI ──
function ItopNode({ data }: any) {
  const color = typeColor[data.type] || "#1677ff";
  return (
    <div style={{
      background: "#fff", border: `2px solid ${color}`, borderRadius: 10,
      padding: "6px 12px", minWidth: 110, textAlign: "center",
      boxShadow: `0 1px 6px ${color}22`,
    }}>
      <Handle type="target" position={Position.Top} />
      <div style={{ fontSize: 10, color, fontWeight: 700, lineHeight: 1.2 }}>
        {data.typeLabel || data.type}
      </div>
      <div style={{ fontSize: 12, fontWeight: 600, lineHeight: 1.3 }}>{data.label}</div>
      {data.properties?.status && (
        <Tag color={data.properties.status === "production" ? "green" : "default"}
             style={{ fontSize: 9, marginTop: 2, lineHeight: "14px" }}>
          {data.properties.status}
        </Tag>
      )}
      <Handle type="source" position={Position.Bottom} />
    </div>
  );
}

function LocalNode({ data }: any) {
  return (
    <div style={{ background: "#e6f4ff", border: "2px solid #1677ff", borderRadius: 12, padding: "6px 10px", textAlign: "center" }}>
      <Handle type="target" position={Position.Top} />
      <div style={{ fontWeight: 600, fontSize: 12 }}>{data.label}</div>
      <Tag color={data.health === "healthy" ? "green" : "red"} style={{ fontSize: 10, marginTop: 2 }}>{data.health}</Tag>
      <Handle type="source" position={Position.Bottom} />
    </div>
  );
}

export default function TopologyPage() {
  const [appFilter, setAppFilter] = useState<string>("itop");
  const [useItop, setUseItop] = useState(true);
  const [resetKey, setResetKey] = useState(0);

  const { data: itopData, isLoading: itopLoading, refetch: refetchItop } = useQuery({
    queryKey: ["itop-topology", appFilter],
    queryFn: () => apmApi.getAppTopology(appFilter).then(r => r.data),
    enabled: useItop && !!appFilter,
  });

  const { data: localData, isLoading: localLoading } = useQuery({
    queryKey: ["topology"],
    queryFn: () => apmApi.getTopology().then(r => r.data),
    enabled: !useItop,
  });

  const handleRefresh = useCallback(async () => {
    try {
      await apmApi.refreshTopology();
      message.success("已从 iTop 刷新拓扑数据");
      refetchItop();
    } catch {
      message.error("刷新失败，请检查 iTop 数据源连接");
    }
  }, [refetchItop]);

  const handleResetLayout = useCallback(() => {
    setResetKey(k => k + 1);
    message.info("布局已重置");
  }, []);

  const isLoading = useItop ? itopLoading : localLoading;
  const rawData = useItop ? itopData : localData;
  const graph = rawData?.graph;

  // ── convert to ReactFlow format + apply dagre layout ──
  // MUST be before any early return (React hooks order)
  const rawNodes = (graph?.nodes || rawData?.nodes || []).map((n: any) => ({
    id: n.id,
    type: useItop ? "itop" : "local",
    data: n,
  }));
  const rawEdges = (graph?.edges || rawData?.edges || []).map((e: any, i: number) => ({
    id: e.id || `e-${i}`,
    source: e.source,
    target: e.target,
    label: e.label,
    animated: true,
    style: { stroke: "#b0b0b0", strokeWidth: 1.5 },
    markerEnd: { type: MarkerType.ArrowClosed, color: "#b0b0b0" },
  }));

  const nodes = useMemo(
    () => layoutDagre(rawNodes, rawEdges),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [graph, resetKey],
  );
  const edges = rawEdges;
  const hasData = nodes.length > 0;

  if (isLoading) return <Spin size="large" style={{ display: "block", margin: "20vh auto" }} />;

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "calc(100vh - 152px)", minHeight: 400 }}>
      {/* ── header bar ── */}
      <div style={{
        flex: "0 0 auto", padding: "8px 16px", marginBottom: 8,
        border: "1px solid #f0f0f0", borderRadius: 8, background: "#fff",
        display: "flex", alignItems: "center", justifyContent: "space-between",
        flexWrap: "wrap", gap: 8,
      }}>
        <Space><NodeIndexOutlined /><Text strong>服务拓扑</Text></Space>
        <Space>
          <Button size="small" onClick={() => setUseItop(!useItop)}
                  type={useItop ? "primary" : "default"}>
            {useItop ? "iTop 数据源" : "本地数据源"}
          </Button>
          {useItop && (
            <>
              <Select size="small" style={{ width: 140 }} value={appFilter} onChange={setAppFilter}
                options={[
                  { value: "itop", label: "itop 应用" },
                  { value: "CRM", label: "CRM 应用" },
                  { value: "ERP", label: "ERP 应用" },
                  { value: "Sales web site", label: "Sales Web" },
                ]}
              />
              <Tooltip title="从 iTop 重新拉取数据">
                <Button size="small" icon={<ReloadOutlined />} onClick={handleRefresh}>刷新</Button>
              </Tooltip>
              <Tooltip title="重置为自动布局">
                <Button size="small" icon={<AimOutlined />} onClick={handleResetLayout}>重置布局</Button>
              </Tooltip>
            </>
          )}
        </Space>
      </div>

      {/* ── graph area ── */}
      <div style={{
        flex: "1 1 0%", minHeight: 200,
        border: "1px solid #f0f0f0", borderRadius: 8,
        background: "#fafafa", overflow: "hidden",
      }}>
        {!hasData ? (
          <Empty style={{ marginTop: "10%" }}
            description={useItop ? "未找到应用依赖数据，请点击「刷新」从 iTop 获取" : "暂无本地拓扑数据"} />
        ) : (
          <ReactFlow
            key={resetKey}
            nodes={nodes}
            edges={edges}
            nodeTypes={{ itop: ItopNode, local: LocalNode }}
            fitView
            fitViewOptions={{ padding: 0.3 }}
            attributionPosition="bottom-left"
            nodesDraggable
            nodesConnectable={false}
            edgesFocusable={false}
            edgesUpdatable={false}
            deleteKeyCode={null}
            selectionKeyCode={null}
            multiSelectionKeyCode={null}
            panOnDrag={[1, 2]}
            selectNodesOnDrag={false}
          >
            <Background color="#e8e8e8" gap={20} />
            <Controls showInteractive={false} />
          </ReactFlow>
        )}
      </div>

      {/* ── legend bar ── */}
      {useItop && hasData && (
        <div style={{
          flex: "0 0 auto", marginTop: 8, padding: "4px 12px",
          border: "1px solid #f0f0f0", borderRadius: 6, background: "#fff", overflow: "hidden",
        }}>
          <Text type="secondary" style={{ fontSize: 12 }}>图例：</Text>
          <Space wrap size={[4, 0]} style={{ marginLeft: 4 }}>
            {Object.entries(typeColor).map(([k, v]) => (
              <Tag key={k} color={v} style={{ fontSize: 11, margin: 0 }}>{k}</Tag>
            ))}
          </Space>
        </div>
      )}
    </div>
  );
}
