import { Card, Input, Select, DatePicker, Table, Tag, Space, Typography } from "antd";
import { SearchOutlined } from "@ant-design/icons";
import { useState } from "react";

const { Text } = Typography;
const { RangePicker } = DatePicker;

const mockLogs = [
  { key: "1", time: "2026-05-28 10:28:15", device: "CORE-SW-01", level: "CRIT", facility: "local0", message: "CPU utilization exceeded threshold: 95% (5min avg)" },
  { key: "2", time: "2026-05-28 10:28:10", device: "CORE-SW-01", level: "WARN", facility: "local0", message: "OSPF-1: Neighbor 10.1.1.2 state changed from EXSTART to FULL" },
  { key: "3", time: "2026-05-28 10:27:58", device: "SRV-APP-01", level: "ERR", facility: "daemon", message: "PaymentProcessor: DB query timeout after 3000ms, retry 3/3" },
  { key: "4", time: "2026-05-28 10:27:30", device: "SRV-DB-01", level: "WARN", facility: "daemon", message: "Slow query detected: SELECT * FROM orders WHERE status='pending' took 3.15s" },
  { key: "5", time: "2026-05-28 10:26:00", device: "FW-01", level: "INFO", facility: "local1", message: "SSH brute force attack detected from 198.51.100.55, 5000+ attempts" },
];

const levelColor: Record<string, string> = { CRIT: "red", ERR: "red", WARN: "orange", INFO: "blue", DEBUG: "default" };

export default function LogExplorerPage() {
  const [keyword, setKeyword] = useState("");

  const filtered = keyword ? mockLogs.filter((l) => l.message.includes(keyword) || l.device.includes(keyword)) : mockLogs;

  const columns = [
    { title: "时间", dataIndex: "time", key: "time", width: 170 },
    { title: "设备", dataIndex: "device", key: "device", width: 130 },
    { title: "级别", dataIndex: "level", key: "level", width: 70, render: (l: string) => <Tag color={levelColor[l]}>{l}</Tag> },
    { title: "消息", dataIndex: "message", key: "message", ellipsis: true },
  ];

  return (
    <div>
      <Card title={<Space><SearchOutlined />日志检索 (模块 4)</Space>} extra={<Text type="secondary">Demo 展示数据 | 实际部署后对接 Syslog/Filebeat</Text>}>
        <Space style={{ marginBottom: 16, width: "100%" }}>
          <Input prefix={<SearchOutlined />} placeholder="关键字搜索..." value={keyword} onChange={(e) => setKeyword(e.target.value)} style={{ width: 300 }} allowClear />
          <Select placeholder="设备" allowClear style={{ width: 160 }} options={[{ value: "CORE-SW-01", label: "CORE-SW-01" }, { value: "SRV-APP-01", label: "SRV-APP-01" }]} />
          <Select placeholder="日志级别" allowClear style={{ width: 120 }} options={["CRIT", "ERR", "WARN", "INFO"].map((l) => ({ value: l, label: l }))} />
          <RangePicker showTime />
        </Space>
        <Table columns={columns} dataSource={filtered} size="middle" pagination={false} />
      </Card>
    </div>
  );
}
