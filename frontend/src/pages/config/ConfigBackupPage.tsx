import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Table, Card, Button, Tag, message } from "antd";
import { configApi } from "../../api/modules";

export default function ConfigBackupPage() {
  const qc = useQueryClient();
  const { data, isLoading } = useQuery({ queryKey: ["backups"], queryFn: () => configApi.listBackups({ page_size: 100 }).then(r => r.data) });
  const triggerMu = useMutation({ mutationFn: () => configApi.triggerBackup(), onSuccess: () => { qc.invalidateQueries({ queryKey: ["backups"] }); message.success("Backup triggered"); } });
  return (
    <Card title="Config Backups" extra={<Button type="primary" onClick={() => triggerMu.mutate()} loading={triggerMu.isPending}>Trigger Backup</Button>}>
      <Table columns={[
        { title: "Device", dataIndex: "device_id", width: 280 }, { title: "Type", dataIndex: "backup_type", width: 80 },
        { title: "Status", dataIndex: "status", width: 80, render: (s: string) => <Tag color={s==="success"?"green":"red"}>{s}</Tag> },
        { title: "Hash", dataIndex: "config_hash", width: 200, ellipsis: true },
        { title: "Time", dataIndex: "backup_at", render: (t: string) => new Date(t).toLocaleString() },
      ]} dataSource={data?.items || []} rowKey="id" loading={isLoading} size="middle" pagination={{ pageSize: 20 }} />
    </Card>
  );
}
