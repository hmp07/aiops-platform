import { useState, useCallback } from "react";
import { useQuery } from "@tanstack/react-query";
import { Card, Spin, Empty, Select, Button, Space, Tag, message, Row, Col, Typography } from "antd";
import { ReloadOutlined, NodeIndexOutlined } from "@ant-design/icons";
import ReactFlow, { Background, Controls, Handle, Position, MarkerType } from "reactflow";
import "reactflow/dist/style.css";
import { apmApi } from "../../api/modules";

const { Text } = Typography;

// ── node type colors (iTop class → color) ──
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

function ItopNode({ data }: any) {
  const color = typeColor[data.type] || "#1677ff";
  return (
    <div style={{
      background: "#fff", border: `2px solid ${color}`, borderRadius: 10,
      padding: "8px 14px", minWidth: 120, textAlign: "center",
      boxShadow: `0 2px 8px ${color}22`,
    }}>
      <Handle type="target" position={Position.Top} />
      <div style={{ fontSize: 11, color, fontWeight: 700, marginBottom: 2 }}>
        {data.typeLabel || data.type}
      </div>
      <div style={{ fontSize: 13, fontWeight: 600 }}>{data.label}</div>
      {data.properties?.status && (
        <Tag color={data.properties.status === "production" ? "green" : "default"}
             style={{ fontSize: 10, marginTop: 4 }}>
          {data.properties.status}
        </Tag>
      )}
      <Handle type="source" position={Position.Bottom} />
    </div>
  );
}

function LocalNode({ data }: any) {
  return (
    <div style={{ background: "#e6f4ff", border: "2px solid #1677ff", borderRadius: 12, padding: "8px 12px", textAlign: "center" }}>
      <Handle type="target" position={Position.Top} />
      <div style={{ fontWeight: 600, fontSize: 13 }}>{data.label}</div>
      <Tag color={data.health === "healthy" ? "green" : "red"} style={{ fontSize: 11 }}>{data.health}</Tag>
      <Handle type="source" position={Position.Bottom} />
    </div>
  );
}

export default function TopologyPage() {
  const [appFilter, setAppFilter] = useState<string>("itop");
  const [useItop, setUseItop] = useState(true);

  // ── iTop dependency graph ──
  const { data: itopData, isLoading: itopLoading, refetch: refetchItop } = useQuery({
    queryKey: ["itop-topology", appFilter],
    queryFn: () => apmApi.getAppTopology(appFilter).then(r => r.data),
    enabled: useItop && !!appFilter,
  });

  // ── legacy local topology ──
  const { data: localData, isLoading: localLoading } = useQuery({
    queryKey: ["topology"],
    queryFn: () => apmApi.getTopology().then(r => r.data),
    enabled: !useItop,
  });

  const handleRefresh = useCallback(async () => {
    try {
      await apmApi.refreshTopology();
      message.success("Topology refreshed from iTop");
      refetchItop();
    } catch {
      message.error("Refresh failed");
    }
  }, [refetchItop]);

  const isLoading = useItop ? itopLoading : localLoading;
  const data = useItop ? itopData : localData;
  const graph = data?.graph;

  if (isLoading) return <Spin size="large" style={{ display: "block", margin: "200px auto" }} />;

  const nodes = (graph?.nodes || data?.nodes || []).map((n: any, i: number) => ({
    id: n.id,
    type: useItop ? "itop" : "local",
    position: n.position || {
      x: (i % 5) * 180 + 40,
      y: Math.floor(i / 5) * 140 + 40,
    },
    data: n,
  }));

  const edges = (graph?.edges || data?.edges || []).map((e: any, i: number) => ({
    id: e.id || `e-${i}`,
    source: e.source,
    target: e.target,
    label: e.label,
    animated: true,
    style: { stroke: "#b0b0b0", strokeWidth: 1.5 },
    markerEnd: { type: MarkerType.ArrowClosed, color: "#b0b0b0" },
  }));

  return (
    <div>
      <Card
        title={<Space><NodeIndexOutlined />服务拓扑</Space>}
        extra={
          <Space>
            <Button size="small" onClick={() => setUseItop(!useItop)} type={useItop ? "primary" : "default"}>
              {useItop ? "iTop 数据源" : "本地数据源"}
            </Button>
            {useItop && (
              <>
                <Select
                  size="small" style={{ width: 140 }}
                  value={appFilter}
                  onChange={setAppFilter}
                  options={[
                    { value: "itop", label: "itop 应用" },
                    { value: "CRM", label: "CRM 应用" },
                    { value: "ERP", label: "ERP 应用" },
                    { value: "Sales web site", label: "Sales Web" },
                  ]}
                />
                <Button size="small" icon={<ReloadOutlined />} onClick={handleRefresh}>刷新</Button>
              </>
            )}
          </Space>
        }
      >
        {nodes.length === 0 ? (
          <Empty description={useItop ? "未找到应用依赖数据，请点击刷新从 iTop 获取" : "暂无本地拓扑数据"} />
        ) : (
          <div style={{ height: 550, border: "1px solid #f0f0f0", borderRadius: 8, background: "#fafafa" }}>
            <ReactFlow
              nodes={nodes}
              edges={edges}
              nodeTypes={{ itop: ItopNode, local: LocalNode }}
              fitView
              attributionPosition="bottom-left"
            >
              <Background color="#e8e8e8" gap={20} />
              <Controls />
            </ReactFlow>
          </div>
        )}
      </Card>

      {/* Legend */}
      {useItop && nodes.length > 0 && (
        <Card size="small" style={{ marginTop: 12 }}>
          <Text type="secondary" style={{ fontSize: 12 }}>图例：</Text>
          <Space wrap size={[8, 4]} style={{ marginLeft: 8 }}>
            {Object.entries(typeColor).slice(0, 10).map(([k, v]) => (
              <Tag key={k} color={v} style={{ fontSize: 11 }}>{k}</Tag>
            ))}
          </Space>
        </Card>
      )}
    </div>
  );
}
