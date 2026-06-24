import { useParams, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Descriptions, Card, Tag, Button, Space, Spin, Empty } from "antd";
import { ArrowLeftOutlined } from "@ant-design/icons";
import { deviceApi } from "../../api/modules";

export default function DeviceDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { data: device, isLoading } = useQuery({ queryKey: ["device", id], queryFn: () => deviceApi.get(id!).then(r => r.data), enabled: !!id });
  if (isLoading) return <Spin size="large" style={{ display: "block", margin: "200px auto" }} />;
  if (!device) return <Empty description="设备不存在" />;
  return (
    <div>
      <Button icon={<ArrowLeftOutlined />} onClick={() => navigate("/asset")} style={{ marginBottom: 16 }}>返回设备列表</Button>
      <Card>
        <Descriptions title={device.device_name} bordered column={3} size="small">
          <Descriptions.Item label="类型">{device.device_type}</Descriptions.Item>
          <Descriptions.Item label="厂商">{device.vendor}</Descriptions.Item>
          <Descriptions.Item label="型号">{device.model}</Descriptions.Item>
          <Descriptions.Item label="序列号">{device.serial_number || "-"}</Descriptions.Item>
          <Descriptions.Item label="软件版本">{device.software_version || "-"}</Descriptions.Item>
          <Descriptions.Item label="管理IP">{device.management_ip || "-"}</Descriptions.Item>
          <Descriptions.Item label="位置">{device.location || "-"}</Descriptions.Item>
          <Descriptions.Item label="生命周期"><Tag>{device.lifecycle_status}</Tag></Descriptions.Item>
          <Descriptions.Item label="业务系统">{device.business_system || "-"}</Descriptions.Item>
          <Descriptions.Item label="部门">{device.user_department || "-"}</Descriptions.Item>
          <Descriptions.Item label="最近备份">{device.last_backup_status || "-"}</Descriptions.Item>
          <Descriptions.Item label="最近巡检">{device.last_inspection_status || "-"}</Descriptions.Item>
        </Descriptions>
      </Card>
    </div>
  );
}
