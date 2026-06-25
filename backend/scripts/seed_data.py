"""Seed realistic demo data into all tables for frontend display."""
import asyncio, uuid, random
from datetime import datetime, timedelta, timezone

DSN = "postgresql://aiops_user:KEy5TWWwRu86@127.0.0.1:5432/aiops"

now = datetime.now(timezone.utc)
device_ids = [uuid.uuid4() for _ in range(20)]
service_ids = [uuid.uuid4() for _ in range(8)]
channel_id = uuid.uuid4()

DEVICES = [
    ("CORE-SW-01", "switch", "Cisco", "Catalyst 9500-48Y4C", "CAT9500-001", "17.9.4", "10.1.1.1", "A座-3F-核心机房", "A01"),
    ("CORE-SW-02", "switch", "Cisco", "Catalyst 9500-48Y4C", "CAT9500-002", "17.9.4", "10.1.1.2", "A座-3F-核心机房", "A02"),
    ("AGG-SW-01", "switch", "Huawei", "S6730-H48X6C", "HW6730-001", "V200R022", "10.1.2.1", "A座-3F-核心机房", "A03"),
    ("AGG-SW-02", "switch", "Huawei", "S6730-H48X6C", "HW6730-002", "V200R022", "10.1.2.2", "A座-3F-核心机房", "A04"),
    ("ACC-SW-01", "switch", "H3C", "S5560X-54C-EI", "H3C5560-001", "7.1.070", "10.1.3.1", "A座-4F-接入机房", "B01"),
    ("ACC-SW-02", "switch", "H3C", "S5560X-54C-EI", "H3C5560-002", "7.1.070", "10.1.3.2", "A座-5F-接入机房", "B02"),
    ("FW-01", "firewall", "Huawei", "USG6620E", "HWUSG-001", "V600R006", "10.1.0.1", "A座-3F-核心机房", "A05"),
    ("FW-02", "firewall", "Huawei", "USG6620E", "HWUSG-002", "V600R006", "10.1.0.2", "A座-3F-核心机房", "A06"),
    ("ROUTER-01", "router", "Cisco", "ISR 4451", "CISR4451-001", "17.12.2", "10.1.0.254", "A座-3F-核心机房", "A07"),
    ("ROUTER-02", "router", "Huawei", "NetEngine 8000 M8", "HWNE8000-001", "V800R012", "10.1.0.253", "A座-3F-核心机房", "A08"),
    ("SRV-APP-01", "server", "Dell", "PowerEdge R750xs", "DELL-R750-001", "CentOS 7.9", "10.1.10.11", "B座-2F", "C01"),
    ("SRV-APP-02", "server", "Dell", "PowerEdge R750xs", "DELL-R750-002", "CentOS 7.9", "10.1.10.12", "B座-2F", "C02"),
    ("SRV-DB-01", "server", "HPE", "ProLiant DL380 Gen11", "HPE-DL380-001", "Ubuntu 22.04", "10.1.10.21", "B座-2F", "C03"),
    ("SRV-DB-02", "server", "HPE", "ProLiant DL380 Gen11", "HPE-DL380-002", "Ubuntu 22.04", "10.1.10.22", "B座-2F", "C04"),
    ("SRV-REDIS-01", "server", "Inspur", "NF5280M7", "INSPUR-001", "CentOS 7.9", "10.1.10.31", "B座-2F", "C05"),
    ("SRV-MQ-01", "server", "Inspur", "NF5280M7", "INSPUR-002", "CentOS 7.9", "10.1.10.41", "B座-2F", "C06"),
    ("SRV-LOG-01", "server", "Inspur", "NF5280M7", "INSPUR-003", "Ubuntu 22.04", "10.1.10.51", "B座-2F", "C07"),
    ("SRV-GW-01", "server", "Dell", "PowerEdge R650xs", "DELL-R650-001", "Ubuntu 22.04", "10.1.10.1", "B座-2F", "C08"),
    ("CORE-SW-OLD", "switch", "Cisco", "Catalyst 6509-E", "CAT6509-OLD", "15.2(2)E", "10.1.1.3", "A座-3F-核心机房", "A10"),
    ("ACC-SW-03", "switch", "H3C", "S5560X-54C-EI", "H3C5560-003", "7.1.070", "10.1.3.3", "A座-5F", "B05"),
]

ALERTS = [
    ("CORE-SW-01 CPU 飙升至 95%", "critical", "triggered", "zabbix", "核心交换机 CPU 异常，OSPF 邻居震荡导致"),
    ("支付服务 P99 延迟突增至 3500ms", "critical", "acknowledged", "signoz", "orders 表缺失索引导致慢查询"),
    ("AGG-SW-01 CRC 错误率异常", "warning", "triggered", "zabbix", "接口 Gi1/0/24 CRC 错误累积"),
    ("ACC-SW-01 配置备份连续失败", "warning", "triggered", "custom", "SSH 连接超时"),
    ("SRV-DB-01 磁盘使用率达 85%", "warning", "resolved", "zabbix", "已清理归档日志"),
    ("FW-01 并发会话数突破 80%", "warning", "closed", "zabbix", "防火墙会话异常"),
    ("CORE-SW-01 接口短暂 down/up", "info", "suppressed", "zabbix", "已被告警降噪引擎自动压制"),
    ("订单服务 HTTP 健康检查失败", "critical", "resolved", "signoz", "服务已自动恢复"),
    ("ROUTER-01 BGP 邻居 Down", "critical", "resolved", "zabbix", "出口自动切换至 ROUTER-02"),
    ("FW-02 检测到 SSH 暴力破解", "warning", "closed", "zabbix", "防火墙已自动封禁 IP"),
    ("RabbitMQ 消息积压达 50000 条", "warning", "acknowledged", "signoz", "消费者处理速度降低"),
    ("光模块接收光功率降至 -28dBm", "info", "triggered", "zabbix", "接近接收灵敏度下限"),
    ("ROUTER-02 出口流量达 90%", "warning", "closed", "zabbix", "持续超过 30 分钟"),
    ("Redis 内存使用率瞬时 90%", "info", "suppressed", "zabbix", "5 分钟内恢复至 75%"),
    ("日志采集延迟超 5 分钟", "info", "triggered", "custom", "Agent 写入延迟 P99 达 8 分钟"),
]

SERVICES = [
    ("api-gateway", "API Gateway", "Go", 3, 45, 0.01, 1200, "healthy"),
    ("payment-service", "Payment Service", "Java", 4, 3500, 2.3, 380, "critical"),
    ("order-service", "Order Service", "Java", 3, 180, 0.05, 650, "healthy"),
    ("user-service", "User Service", "Python", 2, 55, 0.01, 420, "healthy"),
    ("mysql-db", "MySQL Database", "N/A", 2, 3200, 0.0, 850, "warning"),
    ("redis-cache", "Redis Cache", "N/A", 1, 2, 0.0, 5000, "healthy"),
    ("rabbitmq", "RabbitMQ", "N/A", 1, 8, 0.0, 3000, "warning"),
    ("log-service", "Log Service", "Go", 1, 120, 0.02, 2000, "healthy"),
]

ARTICLES = [
    ("OSPF 邻居震荡排查指南", "case", "OSPF 邻居状态在 FULL 和 DOWN 之间反复切换的排查方法", ["OSPF", "路由", "Cisco"]),
    ("MySQL 慢查询优化手册", "case", "数据库查询耗时超过 1 秒的优化策略", ["MySQL", "慢查询", "索引"]),
    ("交换机光模块故障处理预案", "emergency", "光模块接收光功率异常时的应急处置", ["光模块", "交换机", "链路"]),
    ("Cisco IOS 配置备份命令模板", "template", "Cisco 设备 running-config 备份命令", ["Cisco", "配置备份"]),
    ("支付系统故障应急预案", "emergency", "支付服务故障的应急响应流程", ["支付", "P0", "应急预案"]),
    ("Redis 内存优化实践", "case", "Redis 内存使用率超 80% 优化策略", ["Redis", "内存", "缓存"]),
    ("H3C 交换机常用排查命令", "template", "H3C Comware 平台排障命令集合", ["H3C", "排障", "命令"]),
    ("常见问题: 配置备份失败", "faq", "设备配置备份失败的排查步骤", ["FAQ", "配置备份"]),
    ("网络设备固件升级指南", "case", "固件升级的标准操作流程", ["固件", "变更", "网络"]),
    ("常见问题: 跨层故障定界", "faq", "应用变慢时如何定位是代码/数据库/网络问题", ["FAQ", "排障", "跨层"]),
]

async def seed():
    import asyncpg
    conn = await asyncpg.connect(DSN)

    # Clean existing data
    tables = ["eventwall_events", "eventwall_faults", "agent_tool_calls", "agent_llm_calls",
              "agent_preflight_logs", "agent_pending_actions", "agent_sessions",
              "chat_messages", "chat_sessions", "alerts", "metrics",
              "evidence_snapshots", "calibration_reports", "service_edges",
              "cross_layer_mappings", "apm_services", "ip_allocations", "config_diffs",
              "config_backups", "batch_operations", "knowledge_articles",
              "graph_edges", "graph_nodes", "alert_rules", "notification_policies",
              "notification_channels", "devices", "subnets", "log_entries", "log_sources"]
    for t in tables:
        await conn.execute(f"DELETE FROM {t}")

    # Seed devices
    for i, d in enumerate(DEVICES):
        await conn.execute(
            "INSERT INTO devices (id, device_name, device_type, vendor, model, serial_number, software_version, management_ip, location, cabinet, lifecycle_status, business_system, extra_attrs) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13)",
            device_ids[i], d[0], d[1], d[2], d[3], d[4], d[5], d[6], d[7], d[8],
            "spare" if i >= 18 else "retired" if i == 18 else "in_use",
            ["核心网络","汇聚网络","接入网络","网络安全","出口网络","支付系统","数据库集群","缓存集群","消息队列","日志平台","API网关"][i % 11],
            '{}'
        )
    print(f"Seeded {len(DEVICES)} devices")

    # Seed alert rules
    rule_id = uuid.uuid4()
    await conn.execute("INSERT INTO alert_rules (id, name, rule_type, metric_name, condition, threshold, severity) VALUES ($1,$2,$3,$4,$5,$6,$7)",
        rule_id, "CPU > 90%", "threshold", "cpu_usage", "gt", 90, "critical")
    print("Seeded 1 alert rule")

    # Seed alerts
    for i, a in enumerate(ALERTS):
        did = device_ids[i % len(device_ids)] if i < 5 else (device_ids[random.randint(0, 19)] if random.random() > 0.3 else None)
        await conn.execute(
            "INSERT INTO alerts (id, time, device_id, rule_id, severity, status, title, description, source, root_cause) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)",
            uuid.uuid4(), now - timedelta(hours=random.randint(0, 72)), did,
            rule_id if i == 0 else None, a[1], a[2], a[0], a[4], a[3],
            '{"hypotheses":[{"rank":1,"cause":"OSPF neighbor flapping","probability":0.65}]}' if i == 0 else None
        )
    print(f"Seeded {len(ALERTS)} alerts")

    # Seed subnets
    for cidr, gw, vlan, desc in [("10.1.0.0/16", "10.1.0.1", 100, "Production"), ("192.168.1.0/24", "192.168.1.1", 200, "Office"), ("172.16.0.0/24", "172.16.0.1", 300, "DMZ")]:
        total = 2 ** (32 - int(cidr.split("/")[1]))
        used = random.randint(10, total - 5)
        sid = uuid.uuid4()
        await conn.execute("INSERT INTO subnets (id, cidr, gateway, vlan_id, description, total_ips, used_ips) VALUES ($1,$2,$3,$4,$5,$6,$7)",
            sid, cidr, gw, vlan, desc, total, used)
        # IP allocations
        for j in range(min(used, 15)):
            octets = cidr.split("/")[0].split(".")
            octets[-1] = str(random.randint(2, 254))
            ip = ".".join(octets)
            await conn.execute("INSERT INTO ip_allocations (id, subnet_id, ip_address, status, device_id, source) VALUES ($1,$2,$3,$4,$5,$6)",
                uuid.uuid4(), sid, ip, "allocated" if j < used - 2 else "reserved",
                device_ids[random.randint(0, 19)] if j < used - 3 else None,
                "arp_discovery" if random.random() > 0.4 else "manual")
    print("Seeded 3 subnets + IPs")

    # Seed APM services
    for i, s in enumerate(SERVICES):
        await conn.execute(
            "INSERT INTO apm_services (id, name, display_name, language, instances, p99_latency_ms, error_rate_pct, throughput_rps, health) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9)",
            service_ids[i], s[0], s[1], s[2], s[3], s[4], s[5], s[6], s[7])
    # Service edges
    for src, tgt, lat in [(0, 1, 3500), (0, 2, 180), (0, 3, 55), (1, 4, 3200), (1, 5, 2), (2, 4, 45), (1, 6, 8)]:
        await conn.execute("INSERT INTO service_edges (id, source_service_id, target_service_id, latency_ms, rps) VALUES ($1,$2,$3,$4,$5)",
            uuid.uuid4(), service_ids[src], service_ids[tgt], lat, random.randint(300, 5000))
    print(f"Seeded {len(SERVICES)} services + 7 edges")

    # Seed knowledge articles
    for a in ARTICLES:
        await conn.execute(
            "INSERT INTO knowledge_articles (id, title, article_type, content, tags, source, status, created_by) VALUES ($1,$2,$3,$4,$5,$6,$7,$8)",
            uuid.uuid4(), a[0], a[1], a[2], a[3], "manual", "published", "admin")
    print(f"Seeded {len(ARTICLES)} articles")

    # Seed notification channel
    await conn.execute("INSERT INTO notification_channels (id, channel_type, name, config) VALUES ($1,$2,$3,$4)",
        channel_id, "wecom", "Ops Alert Group", '{"webhook_url":"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=demo"}')
    await conn.execute("INSERT INTO notification_policies (id, name, channel_id, severity_filter) VALUES ($1,$2,$3,$4)",
        uuid.uuid4(), "Critical Alert Policy", channel_id, '["critical"]')
    print("Seeded notification channel + policy")

    # Seed log entries
    log_msgs = [
        ("CORE-SW-01", "CRIT", "CPU utilization exceeded threshold: 95%"),
        ("CORE-SW-01", "WARN", "OSPF-1: Neighbor 10.1.1.2 state changed from FULL to INIT"),
        ("SRV-APP-01", "ERR", "PaymentProcessor: DB query timeout after 3000ms"),
        ("SRV-DB-01", "WARN", "Slow query: SELECT * FROM orders WHERE status='pending' took 3.15s"),
        ("FW-01", "INFO", "SSH brute force attack detected from 198.51.100.55"),
        ("AGG-SW-01", "WARN", "Interface Gi1/0/24 CRC errors exceeded threshold: 15432"),
        ("ROUTER-01", "CRIT", "BGP neighbor 203.0.113.1 state changed to Down"),
        ("SRV-MQ-01", "WARN", "RabbitMQ queue payment.queue depth exceeded 50000"),
    ]
    for host, level, msg in log_msgs:
        await conn.execute("INSERT INTO log_entries (id, time, hostname, severity, message) VALUES ($1,$2,$3,$4,$5)",
            uuid.uuid4(), now - timedelta(minutes=random.randint(5, 480)), host, level, msg)
    print(f"Seeded {len(log_msgs)} log entries")

    # Seed graph nodes for knowledge graph
    for i, d in enumerate(DEVICES[:8]):
        nid = uuid.uuid4()
        await conn.execute("INSERT INTO graph_nodes (id, entity_type, entity_id, module, label) VALUES ($1,$2,$3,$4,$5)",
            nid, "device", str(device_ids[i]), "module1_asset", d[0])
    for i, s in enumerate(SERVICES[:5]):
        nid = uuid.uuid4()
        await conn.execute("INSERT INTO graph_nodes (id, entity_type, entity_id, module, label) VALUES ($1,$2,$3,$4,$5)",
            nid, "service", str(service_ids[i]), "module6_apm", s[1])

    await conn.close()
    print("\nAll seed data inserted!")

asyncio.run(seed())
