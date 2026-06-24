"""Mock data for AIOps Platform Demo — designed to feel like a real IT operations environment."""
import uuid
from datetime import datetime, timedelta
from typing import Any

now = datetime.now()

# ============================================================
# Users
# ============================================================
USERS: list[dict[str, Any]] = [
    {"id": "u1", "username": "admin", "password": "admin123", "display_name": "张管理", "role": "admin", "email": "admin@aiops.cn", "is_active": True, "last_login_at": (now - timedelta(hours=2)).isoformat(), "created_at": "2026-01-15T09:00:00"},
    {"id": "u2", "username": "engineer", "password": "engineer123", "display_name": "李运维", "role": "engineer", "email": "engineer@aiops.cn", "is_active": True, "last_login_at": (now - timedelta(hours=1)).isoformat(), "created_at": "2026-01-20T10:00:00"},
    {"id": "u3", "username": "viewer", "password": "viewer123", "display_name": "王观察", "role": "viewer", "email": "viewer@aiops.cn", "is_active": True, "last_login_at": (now - timedelta(days=1)).isoformat(), "created_at": "2026-02-01T14:00:00"},
]

# ============================================================
# Devices (20 devices across types)
# ============================================================
DEVICES: list[dict[str, Any]] = [
    {"id": "d1", "device_name": "CORE-SW-01", "device_type": "switch", "vendor": "Cisco", "model": "Catalyst 9500-48Y4C", "serial_number": "CAT9500-XYZ001", "software_version": "17.9.4", "management_ip": "10.1.1.1", "location": "A座-3F-核心机房", "cabinet": "A01", "lifecycle_status": "in_use", "business_system": "核心网络", "user_department": "网络运维部", "up_link_device_id": None, "up_link_port": None, "last_backup_status": "success", "last_backup_at": (now - timedelta(hours=6)).isoformat(), "last_inspection_status": "normal", "last_inspection_at": (now - timedelta(hours=12)).isoformat(), "created_at": "2025-06-01T00:00:00"},
    {"id": "d2", "device_name": "CORE-SW-02", "device_type": "switch", "vendor": "Cisco", "model": "Catalyst 9500-48Y4C", "serial_number": "CAT9500-XYZ002", "software_version": "17.9.4", "management_ip": "10.1.1.2", "location": "A座-3F-核心机房", "cabinet": "A02", "lifecycle_status": "in_use", "business_system": "核心网络", "user_department": "网络运维部", "up_link_device_id": None, "up_link_port": None, "last_backup_status": "success", "last_backup_at": (now - timedelta(hours=6)).isoformat(), "last_inspection_status": "normal", "last_inspection_at": (now - timedelta(hours=12)).isoformat(), "created_at": "2025-06-01T00:00:00"},
    {"id": "d3", "device_name": "AGG-SW-01", "device_type": "switch", "vendor": "Huawei", "model": "S6730-H48X6C", "serial_number": "HW6730-2024001", "software_version": "V200R022C00", "management_ip": "10.1.2.1", "location": "A座-3F-核心机房", "cabinet": "A03", "lifecycle_status": "in_use", "business_system": "汇聚网络", "user_department": "网络运维部", "up_link_device_id": "d1", "up_link_port": "Te1/0/1", "last_backup_status": "success", "last_backup_at": (now - timedelta(hours=6)).isoformat(), "last_inspection_status": "warning", "last_inspection_at": (now - timedelta(hours=12)).isoformat(), "created_at": "2025-07-15T00:00:00"},
    {"id": "d4", "device_name": "AGG-SW-02", "device_type": "switch", "vendor": "Huawei", "model": "S6730-H48X6C", "serial_number": "HW6730-2024002", "software_version": "V200R022C00", "management_ip": "10.1.2.2", "location": "A座-3F-核心机房", "cabinet": "A04", "lifecycle_status": "in_use", "business_system": "汇聚网络", "user_department": "网络运维部", "up_link_device_id": "d2", "up_link_port": "Te1/0/1", "last_backup_status": "success", "last_backup_at": (now - timedelta(hours=6)).isoformat(), "last_inspection_status": "normal", "last_inspection_at": (now - timedelta(hours=12)).isoformat(), "created_at": "2025-07-15T00:00:00"},
    {"id": "d5", "device_name": "ACC-SW-01", "device_type": "switch", "vendor": "H3C", "model": "S5560X-54C-EI", "serial_number": "H3C5560-3001", "software_version": "7.1.070", "management_ip": "10.1.3.1", "location": "A座-4F-接入机房", "cabinet": "B01", "lifecycle_status": "in_use", "business_system": "接入网络", "user_department": "网络运维部", "up_link_device_id": "d3", "up_link_port": "GE1/0/1", "last_backup_status": "failed", "last_backup_at": (now - timedelta(hours=6)).isoformat(), "last_inspection_status": "abnormal", "last_inspection_at": (now - timedelta(hours=12)).isoformat(), "created_at": "2025-08-01T00:00:00"},
    {"id": "d6", "device_name": "ACC-SW-02", "device_type": "switch", "vendor": "H3C", "model": "S5560X-54C-EI", "serial_number": "H3C5560-3002", "software_version": "7.1.070", "management_ip": "10.1.3.2", "location": "A座-4F-接入机房", "cabinet": "B02", "lifecycle_status": "in_use", "business_system": "接入网络", "user_department": "网络运维部", "up_link_device_id": "d4", "up_link_port": "GE1/0/1", "last_backup_status": "success", "last_backup_at": (now - timedelta(hours=6)).isoformat(), "last_inspection_status": "normal", "last_inspection_at": (now - timedelta(hours=12)).isoformat(), "created_at": "2025-08-01T00:00:00"},
    {"id": "d7", "device_name": "FW-01", "device_type": "firewall", "vendor": "Huawei", "model": "USG6620E", "serial_number": "HWUSG-2024001", "software_version": "V600R006C00", "management_ip": "10.1.0.1", "location": "A座-3F-核心机房", "cabinet": "A05", "lifecycle_status": "in_use", "business_system": "网络安全", "user_department": "安全运维部", "up_link_device_id": "d1", "up_link_port": "Te1/0/48", "last_backup_status": "success", "last_backup_at": (now - timedelta(hours=6)).isoformat(), "last_inspection_status": "normal", "last_inspection_at": (now - timedelta(hours=12)).isoformat(), "created_at": "2025-08-15T00:00:00"},
    {"id": "d8", "device_name": "FW-02", "device_type": "firewall", "vendor": "Huawei", "model": "USG6620E", "serial_number": "HWUSG-2024002", "software_version": "V600R006C00", "management_ip": "10.1.0.2", "location": "A座-3F-核心机房", "cabinet": "A06", "lifecycle_status": "in_use", "business_system": "网络安全", "user_department": "安全运维部", "up_link_device_id": "d2", "up_link_port": "Te1/0/48", "last_backup_status": "success", "last_backup_at": (now - timedelta(hours=6)).isoformat(), "last_inspection_status": "normal", "last_inspection_at": (now - timedelta(hours=12)).isoformat(), "created_at": "2025-08-15T00:00:00"},
    {"id": "d9", "device_name": "ROUTER-01", "device_type": "router", "vendor": "Cisco", "model": "ISR 4451", "serial_number": "CISR4451-1001", "software_version": "17.12.2", "management_ip": "10.1.0.254", "location": "A座-3F-核心机房", "cabinet": "A07", "lifecycle_status": "in_use", "business_system": "出口网络", "user_department": "网络运维部", "up_link_device_id": "d1", "up_link_port": "Te1/0/47", "last_backup_status": "success", "last_backup_at": (now - timedelta(hours=6)).isoformat(), "last_inspection_status": "normal", "last_inspection_at": (now - timedelta(hours=12)).isoformat(), "created_at": "2025-06-01T00:00:00"},
    {"id": "d10", "device_name": "ROUTER-02", "device_type": "router", "vendor": "Huawei", "model": "NetEngine 8000 M8", "serial_number": "HWNE8000-2001", "software_version": "V800R012C00", "management_ip": "10.1.0.253", "location": "A座-3F-核心机房", "cabinet": "A08", "lifecycle_status": "in_use", "business_system": "出口网络", "user_department": "网络运维部", "up_link_device_id": "d2", "up_link_port": "Te1/0/47", "last_backup_status": "success", "last_backup_at": (now - timedelta(hours=6)).isoformat(), "last_inspection_status": "normal", "last_inspection_at": (now - timedelta(hours=12)).isoformat(), "created_at": "2025-07-01T00:00:00"},
    {"id": "d11", "device_name": "SRV-APP-01", "device_type": "server", "vendor": "Dell", "model": "PowerEdge R750xs", "serial_number": "DELL-R750-001", "software_version": "CentOS 7.9", "management_ip": "10.1.10.11", "location": "B座-2F-服务器机房", "cabinet": "C01", "lifecycle_status": "in_use", "business_system": "支付系统", "user_department": "应用运维部", "up_link_device_id": "d5", "up_link_port": "GE1/0/10", "last_backup_status": None, "last_backup_at": None, "last_inspection_status": "normal", "last_inspection_at": (now - timedelta(hours=12)).isoformat(), "created_at": "2025-09-01T00:00:00"},
    {"id": "d12", "device_name": "SRV-APP-02", "device_type": "server", "vendor": "Dell", "model": "PowerEdge R750xs", "serial_number": "DELL-R750-002", "software_version": "CentOS 7.9", "management_ip": "10.1.10.12", "location": "B座-2F-服务器机房", "cabinet": "C02", "lifecycle_status": "in_use", "business_system": "支付系统", "user_department": "应用运维部", "up_link_device_id": "d5", "up_link_port": "GE1/0/11", "last_backup_status": None, "last_backup_at": None, "last_inspection_status": "normal", "last_inspection_at": (now - timedelta(hours=12)).isoformat(), "created_at": "2025-09-01T00:00:00"},
    {"id": "d13", "device_name": "SRV-DB-01", "device_type": "server", "vendor": "HPE", "model": "ProLiant DL380 Gen11", "serial_number": "HPE-DL380-001", "software_version": "Ubuntu 22.04 LTS", "management_ip": "10.1.10.21", "location": "B座-2F-服务器机房", "cabinet": "C03", "lifecycle_status": "in_use", "business_system": "数据库集群", "user_department": "DBA 团队", "up_link_device_id": "d5", "up_link_port": "GE1/0/20", "last_backup_status": None, "last_backup_at": None, "last_inspection_status": "warning", "last_inspection_at": (now - timedelta(hours=12)).isoformat(), "created_at": "2025-09-15T00:00:00"},
    {"id": "d14", "device_name": "SRV-DB-02", "device_type": "server", "vendor": "HPE", "model": "ProLiant DL380 Gen11", "serial_number": "HPE-DL380-002", "software_version": "Ubuntu 22.04 LTS", "management_ip": "10.1.10.22", "location": "B座-2F-服务器机房", "cabinet": "C04", "lifecycle_status": "in_use", "business_system": "数据库集群", "user_department": "DBA 团队", "up_link_device_id": "d5", "up_link_port": "GE1/0/21", "last_backup_status": None, "last_backup_at": None, "last_inspection_status": "normal", "last_inspection_at": (now - timedelta(hours=12)).isoformat(), "created_at": "2025-09-15T00:00:00"},
    {"id": "d15", "device_name": "SRV-REDIS-01", "device_type": "server", "vendor": "Inspur", "model": "NF5280M7", "serial_number": "INSPUR-5280-001", "software_version": "CentOS 7.9", "management_ip": "10.1.10.31", "location": "B座-2F-服务器机房", "cabinet": "C05", "lifecycle_status": "in_use", "business_system": "缓存集群", "user_department": "应用运维部", "up_link_device_id": "d5", "up_link_port": "GE1/0/30", "last_backup_status": None, "last_backup_at": None, "last_inspection_status": "normal", "last_inspection_at": (now - timedelta(hours=12)).isoformat(), "created_at": "2025-10-01T00:00:00"},
    {"id": "d16", "device_name": "SRV-MQ-01", "device_type": "server", "vendor": "Inspur", "model": "NF5280M7", "serial_number": "INSPUR-5280-002", "software_version": "CentOS 7.9", "management_ip": "10.1.10.41", "location": "B座-2F-服务器机房", "cabinet": "C06", "lifecycle_status": "in_use", "business_system": "消息队列", "user_department": "应用运维部", "up_link_device_id": "d6", "up_link_port": "GE1/0/10", "last_backup_status": None, "last_backup_at": None, "last_inspection_status": "normal", "last_inspection_at": (now - timedelta(hours=12)).isoformat(), "created_at": "2025-10-01T00:00:00"},
    {"id": "d17", "device_name": "SRV-LOG-01", "device_type": "server", "vendor": "Inspur", "model": "NF5280M7", "serial_number": "INSPUR-5280-003", "software_version": "Ubuntu 22.04 LTS", "management_ip": "10.1.10.51", "location": "B座-2F-服务器机房", "cabinet": "C07", "lifecycle_status": "in_use", "business_system": "日志平台", "user_department": "应用运维部", "up_link_device_id": "d6", "up_link_port": "GE1/0/11", "last_backup_status": None, "last_backup_at": None, "last_inspection_status": "normal", "last_inspection_at": (now - timedelta(hours=12)).isoformat(), "created_at": "2025-10-15T00:00:00"},
    {"id": "d18", "device_name": "CORE-SW-OLD", "device_type": "switch", "vendor": "Cisco", "model": "Catalyst 6509-E", "serial_number": "CAT6509-OLD001", "software_version": "15.2(2)E", "management_ip": "10.1.1.3", "location": "A座-3F-核心机房", "cabinet": "A10", "lifecycle_status": "retired", "business_system": "核心网络[退役]", "user_department": "网络运维部", "up_link_device_id": None, "up_link_port": None, "last_backup_status": "success", "last_backup_at": (now - timedelta(days=90)).isoformat(), "last_inspection_status": None, "last_inspection_at": None, "created_at": "2020-03-01T00:00:00"},
    {"id": "d19", "device_name": "SRV-GW-01", "device_type": "server", "vendor": "Dell", "model": "PowerEdge R650xs", "serial_number": "DELL-R650-001", "software_version": "Ubuntu 22.04 LTS", "management_ip": "10.1.10.1", "location": "B座-2F-服务器机房", "cabinet": "C08", "lifecycle_status": "in_use", "business_system": "API 网关", "user_department": "应用运维部", "up_link_device_id": "d5", "up_link_port": "GE1/0/1", "last_backup_status": None, "last_backup_at": None, "last_inspection_status": "normal", "last_inspection_at": (now - timedelta(hours=12)).isoformat(), "created_at": "2025-09-01T00:00:00"},
    {"id": "d20", "device_name": "ACC-SW-03", "device_type": "switch", "vendor": "H3C", "model": "S5560X-54C-EI", "serial_number": "H3C5560-3003", "software_version": "7.1.070", "management_ip": "10.1.3.3", "location": "A座-5F-接入机房", "cabinet": "B05", "lifecycle_status": "spare", "business_system": "接入网络[备件]", "user_department": "网络运维部", "up_link_device_id": None, "up_link_port": None, "last_backup_status": "success", "last_backup_at": (now - timedelta(days=7)).isoformat(), "last_inspection_status": "normal", "last_inspection_at": (now - timedelta(days=7)).isoformat(), "created_at": "2025-08-01T00:00:00"},
]

# ============================================================
# IPAM — Subnets & Allocations
# ============================================================
SUBNETS: list[dict[str, Any]] = [
    {"id": "s1", "cidr": "10.1.0.0/16", "vlan_id": 100, "gateway": "10.1.0.1", "description": "生产网络-核心区", "total_ips": 65536, "used_ips": 2340, "created_at": "2025-06-01T00:00:00"},
    {"id": "s2", "cidr": "192.168.1.0/24", "vlan_id": 200, "gateway": "192.168.1.1", "description": "办公网络", "total_ips": 256, "used_ips": 223, "created_at": "2025-06-01T00:00:00"},
    {"id": "s3", "cidr": "172.16.0.0/24", "vlan_id": 300, "gateway": "172.16.0.1", "description": "DMZ 区域", "total_ips": 256, "used_ips": 18, "created_at": "2025-08-15T00:00:00"},
]

IP_ALLOCATIONS: list[dict[str, Any]] = [
    {"id": "ip1", "subnet_id": "s1", "ip_address": "10.1.1.1", "status": "allocated", "device_id": "d1", "interface_name": "Vlan100", "source": "arp_discovery", "allocated_at": "2025-06-01T00:00:00"},
    {"id": "ip2", "subnet_id": "s1", "ip_address": "10.1.1.2", "status": "allocated", "device_id": "d2", "interface_name": "Vlan100", "source": "arp_discovery", "allocated_at": "2025-06-01T00:00:00"},
    {"id": "ip3", "subnet_id": "s1", "ip_address": "10.1.2.1", "status": "allocated", "device_id": "d3", "interface_name": "Vlan101", "source": "arp_discovery", "allocated_at": "2025-07-15T00:00:00"},
    {"id": "ip4", "subnet_id": "s1", "ip_address": "10.1.10.11", "status": "allocated", "device_id": "d11", "interface_name": "eth0", "source": "arp_discovery", "allocated_at": "2025-09-01T00:00:00"},
    {"id": "ip5", "subnet_id": "s1", "ip_address": "10.1.10.50", "status": "reserved", "device_id": None, "interface_name": None, "source": "manual", "allocated_at": None},
    {"id": "ip6", "subnet_id": "s1", "ip_address": "10.1.10.100", "status": "free", "device_id": None, "interface_name": None, "source": "manual", "allocated_at": None},
    {"id": "ip7", "subnet_id": "s1", "ip_address": "10.1.10.199", "status": "allocated", "device_id": None, "interface_name": None, "source": "arp_discovery", "allocated_at": (now - timedelta(days=1)).isoformat()},
    {"id": "ip8", "subnet_id": "s1", "ip_address": "10.1.10.200", "status": "allocated", "device_id": None, "interface_name": None, "source": "arp_discovery", "allocated_at": (now - timedelta(days=1)).isoformat()},
    {"id": "ip9", "subnet_id": "s2", "ip_address": "192.168.1.100", "status": "allocated", "device_id": None, "interface_name": None, "source": "arp_discovery", "allocated_at": "2025-08-01T00:00:00"},
    {"id": "ip10", "subnet_id": "s2", "ip_address": "192.168.1.200", "status": "reserved", "device_id": None, "interface_name": None, "source": "manual", "allocated_at": None},
]

# ============================================================
# Alerts — 15 alerts with different states
# ============================================================
ALERTS: list[dict[str, Any]] = [
    {
        "id": "a1", "time": (now - timedelta(hours=2)).isoformat(), "device_id": "d1", "device_name": "CORE-SW-01",
        "rule_name": "CPU 使用率过高", "severity": "critical", "status": "acknowledged",
        "title": "CORE-SW-01 CPU 飙升至 95%",
        "description": "核心交换机 CORE-SW-01 的 CPU 使用率在过去 5 分钟内持续高于 90%，当前值为 95%。该设备承载核心路由协议和 VLAN 间路由，CPU 过高可能导致全网路由收敛异常。",
        "source": "zabbix", "assigned_to": "u2",
        "evidence": {
            "config_snapshot": {
                "device": "CORE-SW-01", "timestamp": (now - timedelta(hours=6)).isoformat(),
                "recent_changes": [
                    {"time": (now - timedelta(hours=4)).isoformat(), "type": "OSPF 配置修改", "detail": "router ospf 1\n network 10.1.0.0 0.0.255.255 area 0\n passive-interface default\n no passive-interface Vlan100", "operator": "李运维"},
                ],
                "snippet": "interface Vlan100\n ip address 10.1.1.1 255.255.0.0\n ip ospf 1 area 0\n!\nrouter ospf 1\n router-id 10.1.1.1\n network 10.1.0.0 0.0.255.255 area 0\n maximum-paths 4\n!"
            },
            "log_fragment": [
                {"time": (now - timedelta(hours=2, minutes=5)).isoformat(), "level": "WARN", "message": "OSPF-1: Neighbor 10.1.1.2 state changed from FULL to INIT"},
                {"time": (now - timedelta(hours=2, minutes=4)).isoformat(), "level": "WARN", "message": "OSPF-1: Neighbor 10.1.1.2 state changed from INIT to EXSTART"},
                {"time": (now - timedelta(hours=2, minutes=2)).isoformat(), "level": "WARN", "message": "OSPF-1: Neighbor 10.1.1.2 state changed from EXSTART to FULL"},
                {"time": (now - timedelta(hours=2, minutes=1)).isoformat(), "level": "CRIT", "message": "CPU utilization exceeded threshold: 95% (5min avg)"},
            ],
            "interface_status": {"GigabitEthernet1/0/1": "up/up", "GigabitEthernet1/0/48": "up/down", "TenGigabitEthernet1/0/1": "up/up"},
        },
        "root_cause": {
            "analysis_time": (now - timedelta(hours=1, minutes=55)).isoformat(),
            "hypotheses": [
                {"rank": 1, "cause": "OSPF 邻居震荡导致路由重新计算，CPU 资源被大量占用", "probability": 0.65, "evidence": ["配置变更记录显示 2 小时前有 OSPF 配置修改", "日志显示 OSPF 邻居状态在告警前 5 分钟内发生 3 次状态切换", "接口 Gi1/0/48 状态 up/down 异常"]},
                {"rank": 2, "cause": "二层环路导致广播风暴，大量帧上送 CPU 处理", "probability": 0.25, "evidence": ["STP 拓扑变更计数在告警前增加", "接入层交换机 ACC-SW-01 同时出现异常流量"]},
                {"rank": 3, "cause": "外部 DDoS 攻击导致设备处理过载", "probability": 0.10, "evidence": ["出口防火墙 FW-01 同时检测到流量异常", "NTP 反射放大攻击特征初现"]},
            ],
            "summary": "综合证据分析，65% 概率为 OSPF 配置变更引发邻居震荡，导致 CPU 飙升至 95%。建议：(1) 检查 Gi1/0/48 连接的光模块和光纤；(2) 回滚 2 小时前的 OSPF 配置修改；(3) 在 OSPF 进程下配置 neighbor 抖动抑制。",
        },
        "timeline": [
            {"time": (now - timedelta(hours=4)).isoformat(), "event": "配置变更: OSPF 配置修改 (操作人: 李运维)", "type": "config_change"},
            {"time": (now - timedelta(hours=2, minutes=10)).isoformat(), "event": "OSPF 邻居 10.1.1.2 状态开始抖动", "type": "anomaly"},
            {"time": (now - timedelta(hours=2, minutes=2)).isoformat(), "event": "CPU 使用率突破 90% 阈值", "type": "threshold_breach"},
            {"time": (now - timedelta(hours=2)).isoformat(), "event": "告警触发: CORE-SW-01 CPU 飙升至 95%", "type": "alert_triggered"},
            {"time": (now - timedelta(hours=1, minutes=58)).isoformat(), "event": "自动取证完成: 采集配置快照 + 日志 + 接口状态", "type": "evidence_collected"},
            {"time": (now - timedelta(hours=1, minutes=55)).isoformat(), "event": "AI 根因分析完成: OSPF 邻居震荡(65%)", "type": "ai_analysis"},
            {"time": (now - timedelta(hours=1)).isoformat(), "event": "工程师李运维认领告警", "type": "acknowledged"},
        ],
    },
    {
        "id": "a2", "time": (now - timedelta(hours=1)).isoformat(), "device_id": "d11", "device_name": "SRV-APP-01",
        "rule_name": "应用响应延迟过高", "severity": "critical", "status": "in_progress",
        "title": "支付服务 P99 延迟突增至 3500ms",
        "description": "支付服务 /api/payment/submit 接口 P99 延迟从正常的 120ms 突增至 3500ms，错误率从 0.01% 升至 2.3%。影响范围：所有支付交易。关联分析显示数据库慢查询数量同步激增。",
        "source": "signoz", "assigned_to": "u2",
        "evidence": {
            "trace_sample": {
                "trace_id": "abc123def456", "duration_ms": 3520,
                "spans": [
                    {"service": "api-gateway", "operation": "POST /api/payment/submit", "duration_ms": 3520, "status": "ok"},
                    {"service": "payment-service", "operation": "processPayment", "duration_ms": 3480, "status": "ok"},
                    {"service": "payment-service", "operation": "db.query", "duration_ms": 3200, "status": "ok"},
                    {"service": "mysql-db", "operation": "SELECT ... FROM orders WHERE ...", "duration_ms": 3150, "status": "ok"},
                ]
            },
            "apm_metrics": {
                "service": "payment-service", "p99_latency_7d": [85, 92, 88, 95, 100, 98, 3500],
                "error_rate_7d": [0.01, 0.01, 0.02, 0.01, 0.01, 0.03, 2.3],
            }
        },
        "root_cause": {
            "analysis_time": (now - timedelta(minutes=55)).isoformat(),
            "hypotheses": [
                {"rank": 1, "cause": "数据库慢查询 — orders 表缺失索引，全表扫描导致查询延迟 3150ms", "probability": 0.75, "evidence": ["Trace 显示 db.query 耗时 3200ms，占总延迟 91%", "数据库服务器 SRV-DB-01 磁盘 IOPS 同步飙升", "慢查询日志显示 SELECT * FROM orders WHERE status='pending' 全表扫描 120 万行"]},
                {"rank": 2, "cause": "网络丢包 — 服务到数据库之间的交换机 ACC-SW-01 接口存在 CRC 错误", "probability": 0.20, "evidence": ["ACC-SW-01 接口 Gi1/0/20 CRC 错误计数增加", "TCP 重传率从 0.1% 升至 1.8%"]},
                {"rank": 3, "cause": "应用代码问题 — 近期发布引入了 N+1 查询", "probability": 0.05, "evidence": ["最近 24h 内有支付服务发布记录", "新版本变更了订单查询 ORM 逻辑"]},
            ],
            "summary": "75% 概率为数据库 orders 表缺失索引导致慢查询。建议：(1) 对 orders 表的 status 字段添加索引；(2) 检查 ORM 生成的 SQL 是否存在 N+1 问题；(3) 确认 ACC-SW-01 Gi1/0/20 接口光模块是否需要更换。",
        },
        "timeline": [
            {"time": (now - timedelta(hours=3)).isoformat(), "event": "支付服务发布 v3.2.1", "type": "deployment"},
            {"time": (now - timedelta(hours=1, minutes=30)).isoformat(), "event": "数据库慢查询数量开始上升", "type": "anomaly"},
            {"time": (now - timedelta(hours=1)).isoformat(), "event": "告警触发: 支付服务 P99 延迟 3500ms", "type": "alert_triggered"},
            {"time": (now - timedelta(minutes=55)).isoformat(), "event": "AI 跨层定界: 75% 数据库问题, 20% 网络问题", "type": "ai_analysis"},
            {"time": (now - timedelta(minutes=30)).isoformat(), "event": "工程师李运维开始处理", "type": "in_progress"},
        ],
    },
    {
        "id": "a3", "time": (now - timedelta(hours=5)).isoformat(), "device_id": "d3", "device_name": "AGG-SW-01",
        "rule_name": "接口错误包过高", "severity": "warning", "status": "triggered",
        "title": "AGG-SW-01 接口 Gi1/0/24 CRC 错误率异常",
        "description": "汇聚交换机 AGG-SW-01 的 Gi1/0/24 接口（连接接入交换机 ACC-SW-01）CRC 错误包在最近 1 小时内累积达到 15432 个，超过阈值 1000 个/小时。该接口承载 4F 办公区所有流量。",
        "source": "zabbix", "assigned_to": None,
        "evidence": {},
        "root_cause": None,
        "timeline": [
            {"time": (now - timedelta(hours=5)).isoformat(), "event": "告警触发: Gi1/0/24 CRC 错误包异常", "type": "alert_triggered"},
        ],
    },
    {
        "id": "a4", "time": (now - timedelta(hours=8)).isoformat(), "device_id": "d5", "device_name": "ACC-SW-01",
        "rule_name": "设备配置备份失败", "severity": "warning", "status": "triggered",
        "title": "ACC-SW-01 配置自动备份连续 3 次失败",
        "description": "接入交换机 ACC-SW-01 最近 3 次配置自动备份均失败，最后一次失败时间: 2026-05-28 04:00。错误原因: SSH 连接超时。请检查设备连通性和 SSH 服务状态。",
        "source": "custom", "assigned_to": None,
        "evidence": {},
        "root_cause": None,
        "timeline": [],
    },
    {
        "id": "a5", "time": (now - timedelta(hours=12)).isoformat(), "device_id": "d13", "device_name": "SRV-DB-01",
        "rule_name": "磁盘使用率过高", "severity": "warning", "status": "resolved",
        "title": "SRV-DB-01 磁盘使用率达到 85%",
        "description": "数据库服务器 SRV-DB-01 的 /data 分区使用率达到 85%（总容量 2TB，已用 1.7TB）。磁盘空间不足可能导致数据库写入失败。",
        "source": "zabbix", "assigned_to": "u2",
        "evidence": {},
        "root_cause": None,
        "timeline": [
            {"time": (now - timedelta(hours=12)).isoformat(), "event": "告警触发: 磁盘使用率 85%", "type": "alert_triggered"},
            {"time": (now - timedelta(hours=10)).isoformat(), "event": "工程师清理归档日志，使用率降至 62%", "type": "resolved"},
        ],
    },
    {
        "id": "a6", "time": (now - timedelta(days=1, hours=3)).isoformat(), "device_id": "d7", "device_name": "FW-01",
        "rule_name": "防火墙会话数异常", "severity": "warning", "status": "closed",
        "title": "FW-01 并发会话数突破 80% 阈值",
        "description": "防火墙 FW-01 并发会话数达到 800,000（最大支持 1,000,000），较基线增长 300%。",
        "source": "zabbix", "assigned_to": "u2",
        "evidence": {},
        "root_cause": None,
        "timeline": [],
    },
    {
        "id": "a7", "time": (now - timedelta(hours=3)).isoformat(), "device_id": "d1", "device_name": "CORE-SW-01",
        "rule_name": "接口 down", "severity": "info", "status": "suppressed",
        "title": "CORE-SW-01 接口 Gi2/0/5 短暂 down/up",
        "description": "核心交换机 CORE-SW-01 Gi2/0/5 接口在 5 秒内 down→up 恢复。该事件已被告警降噪引擎(C3.7)自动压制。",
        "source": "zabbix", "assigned_to": None,
        "evidence": {},
        "root_cause": None,
        "timeline": [],
    },
    {
        "id": "a8", "time": (now - timedelta(days=2)).isoformat(), "device_id": "d12", "device_name": "SRV-APP-02",
        "rule_name": "服务不可用", "severity": "critical", "status": "resolved",
        "title": "订单服务 HTTP 健康检查连续失败",
        "description": "订单服务 /health 端点连续 3 次返回 503，服务已被自动摘除流量。",
        "source": "signoz", "assigned_to": "u2",
        "evidence": {},
        "root_cause": None,
        "timeline": [],
    },
    {
        "id": "a9", "time": (now - timedelta(hours=6)).isoformat(), "device_id": "d9", "device_name": "ROUTER-01",
        "rule_name": "BGP 邻居 down", "severity": "critical", "status": "resolved",
        "title": "ROUTER-01 BGP 邻居 203.0.113.1 状态 Down",
        "description": "出口路由器 ROUTER-01 与 ISP 的 BGP 邻居 203.0.113.1 状态变为 Down，互联网出口流量自动切换至 ROUTER-02。",
        "source": "zabbix", "assigned_to": "u2",
        "evidence": {},
        "root_cause": None,
        "timeline": [],
    },
    {"id": "a10", "time": (now - timedelta(days=1)).isoformat(), "device_id": "d8", "device_name": "FW-02", "rule_name": "安全事件: 暴力破解", "severity": "warning", "status": "closed", "title": "FW-02 检测到 SSH 暴力破解攻击", "description": "来源 IP 198.51.100.55 在 30 分钟内对 3 台服务器发起 5000+ 次 SSH 登录尝试。防火墙已自动封禁该 IP。", "source": "zabbix", "assigned_to": "u2", "evidence": {}, "root_cause": None, "timeline": []},
    {"id": "a11", "time": (now - timedelta(hours=4)).isoformat(), "device_id": "d16", "device_name": "SRV-MQ-01", "rule_name": "消息积压", "severity": "warning", "status": "acknowledged", "title": "RabbitMQ 消息积压达到 50,000 条", "description": "消息队列 payment.queue 积压消息达到 50,000 条，消费者处理速度降低 80%。", "source": "signoz", "assigned_to": "u2", "evidence": {}, "root_cause": None, "timeline": []},
    {"id": "a12", "time": (now - timedelta(hours=1, minutes=30)).isoformat(), "device_id": "d4", "device_name": "AGG-SW-02", "rule_name": "光模块光功率过低", "severity": "info", "status": "triggered", "title": "AGG-SW-02 Te1/0/3 光模块接收光功率降至 -28dBm", "description": "光模块接收光功率为 -28dBm，接近接收灵敏度下限 -30dBm，存在链路中断风险。", "source": "zabbix", "assigned_to": None, "evidence": {}, "root_cause": None, "timeline": []},
    {"id": "a13", "time": (now - timedelta(days=3)).isoformat(), "device_id": "d10", "device_name": "ROUTER-02", "rule_name": "接口流量超阈值", "severity": "warning", "status": "closed", "title": "ROUTER-02 出口流量达到带宽 90%", "description": "出口路由器 ROUTER-02 出口接口流量达到 9Gbps（总带宽 10Gbps），持续时间超过 30 分钟。", "source": "zabbix", "assigned_to": "u2", "evidence": {}, "root_cause": None, "timeline": []},
    {"id": "a14", "time": (now - timedelta(minutes=30)).isoformat(), "device_id": "d15", "device_name": "SRV-REDIS-01", "rule_name": "内存使用率过高", "severity": "info", "status": "suppressed", "title": "SRV-REDIS-01 内存使用率达到 90%", "description": "Redis 实例内存使用率达到 90%，但仍在 maxmemory 范围内。该告警被降噪引擎压制（原因：瞬时波动，5 分钟内已恢复至 75%）。", "source": "zabbix", "assigned_to": None, "evidence": {}, "root_cause": None, "timeline": []},
    {"id": "a15", "time": (now - timedelta(hours=2, minutes=30)).isoformat(), "device_id": "d17", "device_name": "SRV-LOG-01", "rule_name": "日志采集延迟", "severity": "info", "status": "triggered", "title": "SRV-LOG-01 日志采集延迟超过 5 分钟", "description": "日志采集 Agent 到日志平台的写入延迟 P99 达到 8 分钟，正常应 < 30 秒。可能影响实时告警的日志取证时效。", "source": "custom", "assigned_to": None, "evidence": {}, "root_cause": None, "timeline": []},
]

# ============================================================
# Config Backups & Diffs
# ============================================================
CONFIG_BACKUPS: list[dict[str, Any]] = [
    {"id": "cb1", "device_id": "d1", "device_name": "CORE-SW-01", "backup_type": "scheduled", "status": "success", "file_size": 48200, "backup_at": (now - timedelta(hours=6)).isoformat(), "config_hash": "sha256:abc123"},
    {"id": "cb2", "device_id": "d1", "device_name": "CORE-SW-01", "backup_type": "manual", "status": "success", "file_size": 47800, "backup_at": (now - timedelta(days=1)).isoformat(), "config_hash": "sha256:def456"},
    {"id": "cb3", "device_id": "d3", "device_name": "AGG-SW-01", "backup_type": "scheduled", "status": "success", "file_size": 32100, "backup_at": (now - timedelta(hours=6)).isoformat(), "config_hash": "sha256:ghi789"},
    {"id": "cb4", "device_id": "d5", "device_name": "ACC-SW-01", "backup_type": "scheduled", "status": "failed", "file_size": 0, "backup_at": (now - timedelta(hours=6)).isoformat(), "config_hash": None},
    {"id": "cb5", "device_id": "d7", "device_name": "FW-01", "backup_type": "scheduled", "status": "success", "file_size": 28400, "backup_at": (now - timedelta(hours=6)).isoformat(), "config_hash": "sha256:jkl012"},
]

CONFIG_DIFF = {
    "device_id": "d1",
    "device_name": "CORE-SW-01",
    "old_backup_at": (now - timedelta(days=1)).isoformat(),
    "new_backup_at": (now - timedelta(hours=6)).isoformat(),
    "old_content": """!
hostname CORE-SW-01
!
interface GigabitEthernet1/0/1
 description Uplink to CORE-SW-02
 switchport mode trunk
!
interface GigabitEthernet1/0/48
 description Connection to FW-01
 switchport mode trunk
!
router ospf 1
 router-id 10.1.1.1
 network 10.1.0.0 0.0.255.255 area 0
 passive-interface default
 no passive-interface GigabitEthernet1/0/1
 maximum-paths 4
!
end""",
    "new_content": """!
hostname CORE-SW-01
!
interface GigabitEthernet1/0/1
 description Uplink to CORE-SW-02
 switchport mode trunk
!
interface GigabitEthernet1/0/48
 description Connection to FW-01
 switchport mode trunk
 shutdown
!
router ospf 1
 router-id 10.1.1.1
 network 10.1.0.0 0.0.255.255 area 0
 passive-interface default
 no passive-interface GigabitEthernet1/0/1
 no passive-interface Vlan100
 maximum-paths 4
!
end""",
    "risk_analysis": {
        "risk_level": "high",
        "reasons": [
            "发现高危变更: Gi1/0/48 接口被 shutdown（该接口为防火墙上联，下线将导致全网断网）",
            "OSPF passive-interface 配置变更: 新增 no passive-interface Vlan100（影响路由协议行为）",
            "变更发生在非变更窗口（变更窗口: 每周六 02:00-06:00）",
        ],
        "suggestion": "该变更为异常高危变更，建议立即确认: (1) Gi1/0/48 shutdown 是否为误操作；(2) OSPF 配置更改是否经过审批。如非授权操作，请立即回滚。",
    },
}

# ============================================================
# APM — Services & Topology
# ============================================================
SERVICES: list[dict[str, Any]] = [
    {"id": "sv1", "name": "api-gateway", "display_name": "API 网关", "language": "Go", "instances": 3, "host_ids": ["d19"], "p99_latency_ms": 45, "error_rate_pct": 0.01, "throughput_rps": 1200, "health": "healthy"},
    {"id": "sv2", "name": "payment-service", "display_name": "支付服务", "language": "Java", "instances": 4, "host_ids": ["d11", "d12"], "p99_latency_ms": 3500, "error_rate_pct": 2.3, "throughput_rps": 380, "health": "critical"},
    {"id": "sv3", "name": "order-service", "display_name": "订单服务", "language": "Java", "instances": 3, "host_ids": ["d11", "d12"], "p99_latency_ms": 180, "error_rate_pct": 0.05, "throughput_rps": 650, "health": "healthy"},
    {"id": "sv4", "name": "user-service", "display_name": "用户服务", "language": "Python", "instances": 2, "host_ids": ["d11"], "p99_latency_ms": 55, "error_rate_pct": 0.01, "throughput_rps": 420, "health": "healthy"},
    {"id": "sv5", "name": "mysql-db", "display_name": "MySQL 数据库", "language": "N/A", "instances": 2, "host_ids": ["d13", "d14"], "p99_latency_ms": 3200, "error_rate_pct": 0.0, "throughput_rps": 850, "health": "warning"},
    {"id": "sv6", "name": "redis-cache", "display_name": "Redis 缓存", "language": "N/A", "instances": 1, "host_ids": ["d15"], "p99_latency_ms": 2, "error_rate_pct": 0.0, "throughput_rps": 5000, "health": "healthy"},
    {"id": "sv7", "name": "rabbitmq", "display_name": "消息队列", "language": "N/A", "instances": 1, "host_ids": ["d16"], "p99_latency_ms": 8, "error_rate_pct": 0.0, "throughput_rps": 3000, "health": "warning"},
    {"id": "sv8", "name": "log-service", "display_name": "日志服务", "language": "Go", "instances": 1, "host_ids": ["d17"], "p99_latency_ms": 120, "error_rate_pct": 0.02, "throughput_rps": 2000, "health": "healthy"},
]

SERVICE_TOPOLOGY = {
    "nodes": [
        {"id": "api-gateway", "label": "API 网关", "type": "service", "health": "healthy", "layer": "application"},
        {"id": "payment-service", "label": "支付服务", "type": "service", "health": "critical", "layer": "application"},
        {"id": "order-service", "label": "订单服务", "type": "service", "health": "healthy", "layer": "application"},
        {"id": "user-service", "label": "用户服务", "type": "service", "health": "healthy", "layer": "application"},
        {"id": "mysql-db", "label": "MySQL", "type": "database", "health": "warning", "layer": "application"},
        {"id": "redis-cache", "label": "Redis", "type": "cache", "health": "healthy", "layer": "application"},
        {"id": "rabbitmq", "label": "RabbitMQ", "type": "queue", "health": "warning", "layer": "application"},
        {"id": "srv-db-01", "label": "SRV-DB-01", "type": "host", "health": "warning", "layer": "infrastructure"},
        {"id": "srv-app-01", "label": "SRV-APP-01", "type": "host", "health": "healthy", "layer": "infrastructure"},
        {"id": "srv-redis-01", "label": "SRV-REDIS-01", "type": "host", "health": "healthy", "layer": "infrastructure"},
        {"id": "acc-sw-01", "label": "ACC-SW-01", "type": "switch", "health": "warning", "layer": "network"},
    ],
    "edges": [
        {"source": "api-gateway", "target": "payment-service", "latency_ms": 3500, "rps": 380, "status": "critical"},
        {"source": "api-gateway", "target": "order-service", "latency_ms": 180, "rps": 650, "status": "healthy"},
        {"source": "api-gateway", "target": "user-service", "latency_ms": 55, "rps": 420, "status": "healthy"},
        {"source": "payment-service", "target": "mysql-db", "latency_ms": 3200, "rps": 850, "status": "critical"},
        {"source": "payment-service", "target": "redis-cache", "latency_ms": 2, "rps": 5000, "status": "healthy"},
        {"source": "order-service", "target": "mysql-db", "latency_ms": 45, "rps": 600, "status": "healthy"},
        {"source": "payment-service", "target": "rabbitmq", "latency_ms": 8, "rps": 3000, "status": "warning"},
        {"source": "mysql-db", "target": "srv-db-01", "latency_ms": 0, "rps": 0, "status": "healthy"},
        {"source": "payment-service", "target": "srv-app-01", "latency_ms": 0, "rps": 0, "status": "healthy"},
        {"source": "redis-cache", "target": "srv-redis-01", "latency_ms": 0, "rps": 0, "status": "healthy"},
        {"source": "srv-db-01", "target": "acc-sw-01", "latency_ms": 0, "rps": 0, "status": "healthy"},
        {"source": "srv-app-01", "target": "acc-sw-01", "latency_ms": 0, "rps": 0, "status": "healthy"},
        {"source": "srv-redis-01", "target": "acc-sw-01", "latency_ms": 0, "rps": 0, "status": "healthy"},
    ],
}

CROSS_LAYER_DIAGNOSIS = {
    "alert_id": "a2",
    "analysis": {
        "fault_boundary": "75% 应用层 → 数据库问题, 20% 基础设施层 → 网络问题, 5% 应用层 → 代码问题",
        "confidence": 0.85,
        "layers": {
            "application_code": {"probability": 0.05, "finding": "支付服务 v3.2.1 发布变更了 ORM 查询逻辑，存在 N+1 查询风险", "action": "检查 ORM 日志，确认是否存在 N+1"},
            "database": {"probability": 0.75, "finding": "orders 表 status 字段缺失索引，全表扫描 120 万行", "action": "CREATE INDEX idx_orders_status ON orders(status);"},
            "network": {"probability": 0.20, "finding": "ACC-SW-01 Gi1/0/20 CRC 错误增加，TCP 重传率 1.8%", "action": "更换光模块或清洁光纤接头"},
            "host_resource": {"probability": 0.00, "finding": "SRV-DB-01 CPU/内存/磁盘 IO 均在正常范围", "action": "无需操作"},
        },
    },
}

# ============================================================
# AI Inspection Reports
# ============================================================
INSPECTION_REPORTS: list[dict[str, Any]] = [
    {
        "id": "ir1", "title": "第 22 周巡检报告 (2026-05-25 ~ 2026-05-31)", "type": "weekly",
        "generated_at": (now - timedelta(hours=12)).isoformat(), "status": "published",
        "summary": """## 巡检概要
- **巡检设备**: 20 台（在线 19 台，离线 1 台）
- **配置备份成功率**: 85%（17/20，3 台失败）
- **告警总数**: 本周 23 条（较上周下降 35%）
- **应用服务健康**: 6/8 健康，1 个警告，1 个异常

## 重点关注项

### 1. 核心交换机 CORE-SW-01 出现高危告警
- 告警: CPU 飙升至 95%，根因分析判定为 OSPF 邻居震荡（概率 65%）
- 影响: 全网路由收敛风险
- 建议: 检查光纤连接，回滚 OSPF 配置修改，配置 neighbor 抖动抑制

### 2. 支付服务 P99 延迟异常
- 现象: P99 延迟从 120ms 突增至 3500ms，错误率从 0.01% 升至 2.3%
- 根因: 75% 概率为 orders 表缺失索引导致数据库慢查询
- 建议: 对 orders.status 加索引，检查 v3.2.1 发布引入的 ORM 变更

### 3. 子网 IP 使用率告警
- 192.168.1.0/24（办公网）IP 使用率达 87%（223/256），按当前趋势预计 8 周内耗尽
- 建议: 扩容办公网段至 /23 或回收僵尸 IP

### 4. 配置备份失败
- ACC-SW-01（H3C S5560X）连续 3 次备份失败，错误: SSH 连接超时
- 建议: 检查设备 SSH 服务状态和网络连通性

## 本周做得好的
- AI 告警降噪压制了 15 条瞬时抖动告警，减少告警噪声 40%
- 防火墙 FW-02 自动封禁 SSH 暴力破解 IP，响应时间 < 1 分钟
- 知识库新增 3 条故障处理案例（OSPF 排障、慢查询优化、光模块更换）

## 下周需关注
- CORE-SW-01 OSPF 配置修改的审批流程是否到位
- 数据库 orders 表索引优化后的性能改善跟踪
- 办公网 IP 扩容方案评审
""",
    },
    {
        "id": "ir2", "title": "第 21 周巡检报告 (2026-05-18 ~ 2026-05-24)", "type": "weekly",
        "generated_at": (now - timedelta(days=7)).isoformat(), "status": "published",
        "summary": """## 巡检概要
- **巡检设备**: 20 台（全部在线）
- **配置备份成功率**: 100%
- **告警总数**: 35 条
- **应用服务健康**: 7/8 健康，1 个警告

## 重点关注项
1. 出口路由器 ROUTER-02 出口流量达到带宽 90%，需评估扩容需求
2. 防火墙 FW-01 检测到 SSH 暴力破解攻击，已自动封禁
""",
    },
    {
        "id": "ir3", "title": "2026 年 5 月巡检月报", "type": "monthly",
        "generated_at": (now - timedelta(days=2)).isoformat(), "status": "published",
        "summary": "本月巡检月报概要: 整体运维态势稳定，核心网络发生 1 次高危 OSPF 故障(已恢复)，应用层发现 1 次数据库慢查询导致的性能下降(处理中)。AI 告警降噪累计压制 87 条瞬时告警。",
    },
]

# ============================================================
# Knowledge Base
# ============================================================
KNOWLEDGE_ARTICLES: list[dict[str, Any]] = [
    {"id": "k1", "title": "OSPF 邻居震荡排查指南", "article_type": "case", "tags": ["OSPF", "路由协议", "Cisco"], "content": "## 故障现象\nOSPF 邻居状态在 FULL 和 DOWN 之间反复切换，导致路由不断重新计算，CPU 使用率飙升。\n\n## 排查步骤\n1. 检查物理层: show interface <intf> 查看 CRC 错误、光功率\n2. 检查 OSPF 配置一致性: hello/dead 间隔、区域 ID、认证\n3. 检查 MTU: ping <neighbor> size 1500 df-bit\n4. 检查日志: show log | inc OSPF\n\n## 解决方案\n1. 更换故障光模块或光纤\n2. 配置 OSPF neighbor 抖动抑制: ip ospf dead-interval minimal hello-multiplier 5\n3. 在接口下配置: carrier-delay msec 200", "status": "published", "created_at": "2026-05-15T10:00:00"},
    {"id": "k2", "title": "MySQL 慢查询优化手册", "article_type": "case", "tags": ["MySQL", "慢查询", "索引优化"], "content": "## 问题描述\n数据库查询耗时超过 1 秒，导致应用接口响应延迟同步升高。\n\n## 排查方法\n1. 开启慢查询日志: SET GLOBAL slow_query_log = ON; SET long_query_time = 1;\n2. 使用 EXPLAIN 分析执行计划\n3. 检查是否全表扫描: type=ALL 表示全表扫描\n4. 使用 pt-query-digest 分析慢查询日志\n\n## 优化方案\n1. 对 WHERE/JOIN/ORDER BY 字段创建索引\n2. 避免 SELECT *，只查询需要的列\n3. 大表考虑分区或归档历史数据\n4. 检查 ORM 生成的 SQL 是否存在 N+1 查询", "status": "published", "created_at": "2026-05-20T14:00:00"},
    {"id": "k3", "title": "交换机光模块故障处理预案", "article_type": "emergency", "tags": ["光模块", "交换机", "链路故障"], "content": "## 触发条件\n- 接口光功率低于接收灵敏度下限\n- CRC 错误或 input errors 持续增长\n- 链路频繁 up/down\n\n## 应急处置步骤\n1. 确认备用链路状态正常\n2. 将业务流量切换至备用链路\n3. 更换故障光模块（需同型号、同波长）\n4. 如需更换光纤，优先检查光纤接头清洁度\n5. 恢复后观察 30 分钟，确认 CRC 不再增长\n6. 记录事件到故障管理系统", "status": "published", "created_at": "2026-04-10T09:00:00"},
    {"id": "k4", "title": "Cisco IOS 配置备份命令模板", "article_type": "template", "tags": ["Cisco", "配置备份", "命令模板"], "content": "## Cisco IOS 配置备份\n```\ncopy running-config tftp://10.1.10.100/CORE-SW-01-$(date).cfg\nshow running-config\nshow version\nshow inventory\nshow ip interface brief\nshow vlan brief\nshow cdp neighbors detail\n```\n\n## 华为 VRP 等价命令\n```\nsave /backup/config-$(date).cfg\ncopy running-config tftp 10.1.10.100\n```", "status": "published", "created_at": "2026-03-01T10:00:00"},
    {"id": "k5", "title": "常见问题: 设备配置备份失败如何处理？", "article_type": "faq", "tags": ["配置备份", "FAQ"], "content": "**Q: 设备配置备份失败怎么办？**\n\n**A:** 按以下步骤排查:\n1. 确认设备从平台管理网可达: ping <device_ip>\n2. 确认 SSH 端口 22 可达: telnet <device_ip> 22\n3. 检查设备 SSH 配置: show ip ssh / show running-config | inc ssh\n4. 检查备份账号的权限级别（需 privilege level 15）\n5. 检查设备 ACL 是否限制了管理网段的访问\n6. 若为 Telnet 设备（老设备），确认 Telnet 服务已启用", "status": "published", "created_at": "2026-04-20T16:00:00"},
    {"id": "k6", "title": "支付系统故障应急预案", "article_type": "emergency", "tags": ["支付", "应急预案", "P0"], "content": "## 故障等级: P0（影响所有支付交易）\n\n## 应急响应流程\n1. 确认故障范围: 是否所有支付渠道均受影响\n2. 检查依赖服务: 数据库 > 缓存 > 消息队列 > 网络\n3. 一级预案: 切换到备用数据库集群（SRV-DB-02）\n4. 二级预案: 降级为非实时支付（异步处理）\n5. 三级预案: 暂停支付服务，启用人工处理通道\n\n## 恢复后\n- 数据核对: 确保无丢单、无重复扣款\n- 根因分析: 48h 内输出故障报告\n- 预案更新: 根据本次经验完善预案", "status": "published", "created_at": "2026-05-01T08:00:00"},
    {"id": "k7", "title": "Redis 内存优化实践", "article_type": "case", "tags": ["Redis", "内存优化", "缓存"], "content": "Redis 内存使用率超过 80% 时的优化策略。1. 设置合理的 maxmemory-policy；2. 分析大 key 并拆分；3. 过期时间优化；4. 使用 lazyfree-lazy-eviction 避免阻塞。", "status": "published", "created_at": "2026-05-10T11:00:00"},
    {"id": "k8", "title": "H3C 交换机常用排查命令", "article_type": "template", "tags": ["H3C", "命令模板", "排障"], "content": "H3C Comware 平台常用排障命令集合。display device, display interface brief, display logbuffer, display cpu-usage, display memory, display transceiver diagnosis interface, display stp brief, display lldp neighbor-information list。", "status": "published", "created_at": "2026-03-15T14:00:00"},
    {"id": "k9", "title": "网络设备固件升级操作指南", "article_type": "case", "tags": ["固件升级", "变更", "网络"], "content": "网络设备固件升级的标准操作流程。包含升级前准备、备份验证、升级执行、回滚方案、升级后验证。", "status": "draft", "created_at": "2026-05-25T09:00:00"},
    {"id": "k10", "title": "常见问题: 如何快速定位是哪一层的问题？", "article_type": "faq", "tags": ["排障", "FAQ", "跨层"], "content": "**Q: 应用变慢了，怎么快速定位是应用代码问题、数据库问题还是网络问题？**\n\n**A:** 使用平台的 AI 跨层故障定界功能(H8.10):\n1. 从告警详情页点击「跨层分析」\n2. AI 自动关联应用 Trace + 数据库慢查询 + 网络设备指标\n3. 输出分层定界结论（应用层/数据库层/网络层/宿主机层）及置信度\n4. 关联知识库历史案例，给出一键式处理建议", "status": "published", "created_at": "2026-05-25T10:00:00"},
]

# ============================================================
# Audit Logs
# ============================================================
AUDIT_LOGS: list[dict[str, Any]] = [
    {"id": "aud1", "user_id": "u2", "username": "engineer", "action": "login", "resource_type": "auth", "resource_id": None, "detail": "用户登录成功", "ip_address": "192.168.1.100", "created_at": (now - timedelta(hours=2)).isoformat()},
    {"id": "aud2", "user_id": "u2", "username": "engineer", "action": "acknowledge_alert", "resource_type": "alert", "resource_id": "a1", "detail": "认领告警: CORE-SW-01 CPU 飙升至 95%", "ip_address": "192.168.1.100", "created_at": (now - timedelta(hours=1)).isoformat()},
    {"id": "aud3", "user_id": "u2", "username": "engineer", "action": "update_alert", "resource_type": "alert", "resource_id": "a2", "detail": "开始处理告警: 支付服务 P99 延迟突增", "ip_address": "192.168.1.100", "created_at": (now - timedelta(minutes=30)).isoformat()},
    {"id": "aud4", "user_id": "u1", "username": "admin", "action": "create_user", "resource_type": "user", "resource_id": "u3", "detail": "创建用户: viewer (王观察)", "ip_address": "192.168.1.50", "created_at": "2026-02-01T14:00:00"},
    {"id": "aud5", "user_id": "u2", "username": "engineer", "action": "trigger_backup", "resource_type": "config", "resource_id": "d1", "detail": "手动触发 CORE-SW-01 配置备份", "ip_address": "192.168.1.100", "created_at": (now - timedelta(days=1)).isoformat()},
]
