"""RBAC Permission Registry — ~146 permission codes across 11 modules.

Permission code format: {module}:{resource}:{action}

Built-in roles define which codes each role gets.
"""

from dataclasses import dataclass, field

# ============================================================
# Permission Codes — organized by module
# ============================================================

PERMISSION_DEFINITIONS: dict[str, dict] = {
    # ---- Module 1: Asset ----
    "asset:device:list":     {"name": "查看设备列表", "category": "asset", "sort": 1},
    "asset:device:create":   {"name": "创建设备", "category": "asset", "sort": 2},
    "asset:device:retrieve": {"name": "查看设备详情", "category": "asset", "sort": 3},
    "asset:device:update":   {"name": "更新设备信息", "category": "asset", "sort": 4},
    "asset:device:delete":   {"name": "删除设备", "category": "asset", "sort": 5},
    "asset:calibration:list":   {"name": "查看校准报告", "category": "asset", "sort": 6},
    "asset:calibration:execute":{"name": "执行资产校准", "category": "asset", "sort": 7},
    "asset:calibration:approve":{"name": "确认校准差异", "category": "asset", "sort": 8},
    "asset:import:execute":  {"name": "批量导入设备", "category": "asset", "sort": 9},
    "asset:export:execute":  {"name": "导出资产台账", "category": "asset", "sort": 10},

    # ---- Module 2: IPAM ----
    "ipam:subnet:list":     {"name": "查看子网列表", "category": "ipam", "sort": 1},
    "ipam:subnet:create":   {"name": "创建子网", "category": "ipam", "sort": 2},
    "ipam:subnet:update":   {"name": "更新子网", "category": "ipam", "sort": 3},
    "ipam:subnet:delete":   {"name": "删除子网", "category": "ipam", "sort": 4},
    "ipam:ip:list":         {"name": "查看 IP 分配", "category": "ipam", "sort": 5},
    "ipam:ip:allocate":     {"name": "分配 IP", "category": "ipam", "sort": 6},
    "ipam:ip:release":      {"name": "释放 IP", "category": "ipam", "sort": 7},
    "ipam:ip:reserve":      {"name": "保留 IP", "category": "ipam", "sort": 8},
    "ipam:discovery:execute":{"name": "执行 IP 发现", "category": "ipam", "sort": 9},

    # ---- Module 3: Monitoring ----
    "monitoring:alert:list":        {"name": "查看告警列表", "category": "monitoring", "sort": 1},
    "monitoring:alert:retrieve":    {"name": "查看告警详情", "category": "monitoring", "sort": 2},
    "monitoring:alert:acknowledge": {"name": "认领告警", "category": "monitoring", "sort": 3},
    "monitoring:alert:resolve":     {"name": "解决告警", "category": "monitoring", "sort": 4},
    "monitoring:alert:close":       {"name": "关闭告警", "category": "monitoring", "sort": 5},
    "monitoring:alert:delete":      {"name": "删除告警", "category": "monitoring", "sort": 6},
    "monitoring:rule:list":    {"name": "查看告警规则", "category": "monitoring", "sort": 7},
    "monitoring:rule:create":  {"name": "创建告警规则", "category": "monitoring", "sort": 8},
    "monitoring:rule:update":  {"name": "更新告警规则", "category": "monitoring", "sort": 9},
    "monitoring:rule:delete":  {"name": "删除告警规则", "category": "monitoring", "sort": 10},
    "monitoring:metric:list":  {"name": "查看性能指标", "category": "monitoring", "sort": 11},
    "monitoring:metric:export":{"name": "导出指标数据", "category": "monitoring", "sort": 12},
    "monitoring:notification:manage": {"name": "管理通知策略", "category": "monitoring", "sort": 13},
    "monitoring:suppression:manage":  {"name": "管理降噪规则", "category": "monitoring", "sort": 14},

    # ---- Module 4: Log ----
    "log:source:list":   {"name": "查看日志源", "category": "log", "sort": 1},
    "log:source:create": {"name": "创建日志源", "category": "log", "sort": 2},
    "log:source:update": {"name": "更新日志源", "category": "log", "sort": 3},
    "log:source:delete": {"name": "删除日志源", "category": "log", "sort": 4},
    "log:entry:search":  {"name": "搜索日志", "category": "log", "sort": 5},
    "log:entry:ingest":  {"name": "写入日志", "category": "log", "sort": 6},
    "log:entry:export":  {"name": "导出日志", "category": "log", "sort": 7},

    # ---- Module 5: Config ----
    "config:backup:list":    {"name": "查看备份列表", "category": "config", "sort": 1},
    "config:backup:trigger": {"name": "触发配置备份", "category": "config", "sort": 2},
    "config:backup:download":{"name": "下载备份文件", "category": "config", "sort": 3},
    "config:backup:delete":  {"name": "删除备份", "category": "config", "sort": 4},
    "config:diff:view":      {"name": "查看配置差异", "category": "config", "sort": 5},
    "config:rollback:view":  {"name": "查看回滚方案", "category": "config", "sort": 6},
    "config:rollback:execute":{"name": "执行配置回滚", "category": "config", "sort": 7},
    "config:batch:list":     {"name": "查看批量操作", "category": "config", "sort": 8},
    "config:batch:execute":  {"name": "执行批量操作", "category": "config", "sort": 9},

    # ---- Module 6: APM ----
    "apm:service:list":     {"name": "查看服务列表", "category": "apm", "sort": 1},
    "apm:service:retrieve": {"name": "查看服务详情", "category": "apm", "sort": 2},
    "apm:topology:view":    {"name": "查看服务拓扑", "category": "apm", "sort": 3},
    "apm:trace:view":       {"name": "查看链路追踪", "category": "apm", "sort": 4},
    "apm:crosslayer:view":  {"name": "查看跨层分析", "category": "apm", "sort": 5},

    # ---- Module 7: Knowledge ----
    "knowledge:article:list":    {"name": "查看文章列表", "category": "knowledge", "sort": 1},
    "knowledge:article:create":  {"name": "创建文章", "category": "knowledge", "sort": 2},
    "knowledge:article:update":  {"name": "更新文章", "category": "knowledge", "sort": 3},
    "knowledge:article:delete":  {"name": "删除文章", "category": "knowledge", "sort": 4},
    "knowledge:article:publish": {"name": "发布文章", "category": "knowledge", "sort": 5},
    "knowledge:archive:manage":  {"name": "管理自动归档", "category": "knowledge", "sort": 6},
    "knowledge:search:execute":  {"name": "搜索知识库", "category": "knowledge", "sort": 7},

    # ---- Module 8: AI ----
    "ai:chat:send":          {"name": "发送 AI 消息", "category": "ai", "sort": 1},
    "ai:session:list":       {"name": "查看会话列表", "category": "ai", "sort": 2},
    "ai:session:create":     {"name": "创建会话", "category": "ai", "sort": 3},
    "ai:session:delete":     {"name": "删除会话", "category": "ai", "sort": 4},
    "ai:analysis:view":      {"name": "查看分析结果", "category": "ai", "sort": 5},
    "ai:report:view":        {"name": "查看巡检报告", "category": "ai", "sort": 6},
    "ai:report:generate":    {"name": "生成巡检报告", "category": "ai", "sort": 7},
    "ai:skill:manage":       {"name": "管理 Skill", "category": "ai", "sort": 8},
    "ai:provider:manage":    {"name": "管理 LLM 提供商", "category": "ai", "sort": 9},
    "ai:action:confirm":     {"name": "确认待执行动作", "category": "ai", "sort": 10},
    "ai:knowledgegraph:view":{"name": "查看知识图谱", "category": "ai", "sort": 11},
    "ai:audit:view":         {"name": "查看 Agent 审计", "category": "ai", "sort": 12},
    "ai:audit:manage":       {"name": "管理 Agent 审计", "category": "ai", "sort": 13},

    # ---- Module 10: EventWall ----
    "eventwall:event:list":    {"name": "查看事件列表", "category": "eventwall", "sort": 1},
    "eventwall:event:retrieve":{"name": "查看事件详情", "category": "eventwall", "sort": 2},
    "eventwall:fault:list":    {"name": "查看故障分析", "category": "eventwall", "sort": 3},
    "eventwall:fault:resolve": {"name": "解决故障", "category": "eventwall", "sort": 4},
    "eventwall:source:manage": {"name": "管理事件源", "category": "eventwall", "sort": 5},

    # ---- Module 9: Platform (RBAC itself) ----
    "platform:user:list":      {"name": "查看用户列表", "category": "platform", "sort": 1},
    "platform:user:create":    {"name": "创建用户", "category": "platform", "sort": 2},
    "platform:user:update":    {"name": "更新用户", "category": "platform", "sort": 3},
    "platform:user:delete":    {"name": "删除用户", "category": "platform", "sort": 4},
    "platform:role:list":      {"name": "查看角色", "category": "platform", "sort": 5},
    "platform:role:create":    {"name": "创建角色", "category": "platform", "sort": 6},
    "platform:role:update":    {"name": "更新角色", "category": "platform", "sort": 7},
    "platform:role:delete":    {"name": "删除角色", "category": "platform", "sort": 8},
    "platform:permission:list":{"name": "查看权限", "category": "platform", "sort": 9},
    "platform:audit:view":     {"name": "查看审计日志", "category": "platform", "sort": 10},
    "platform:token:manage":   {"name": "管理 API Token", "category": "platform", "sort": 11},
    "platform:module:manage":  {"name": "管理模块可见性", "category": "platform", "sort": 12},
    "platform:task:manage":    {"name": "管理定时任务", "category": "platform", "sort": 13},
}

# ============================================================
# Built-in Roles
# ============================================================

ALL_PERMISSIONS = set(PERMISSION_DEFINITIONS.keys())

BUILTIN_ROLES: dict[str, dict] = {
    "superadmin": {
        "name": "超级管理员",
        "description": "拥有所有权限",
        "permissions": ALL_PERMISSIONS,
    },
    "admin": {
        "name": "管理员",
        "description": "全部模块操作（不含用户管理）",
        "permissions": {
            p for p in ALL_PERMISSIONS
            if not p.startswith("platform:user:") and not p.startswith("platform:role:")
        },
    },
    "operator": {
        "name": "运维操作员",
        "description": "运维模块的读写操作",
        "permissions": {
            p for p in ALL_PERMISSIONS
            if p.startswith(("asset:", "ipam:", "monitoring:", "config:", "apm:", "log:", "knowledge:", "eventwall:event:", "eventwall:fault:"))
            and not p.endswith(":delete")
        },
    },
    "engineer": {
        "name": "运维工程师",
        "description": "标准运维操作（无删除/回滚/高危操作）",
        "permissions": {
            p for p in ALL_PERMISSIONS
            if (
                p.endswith(":list") or p.endswith(":retrieve") or p.endswith(":view")
                or p == "monitoring:alert:acknowledge"
                or p == "monitoring:alert:resolve"
                or p == "config:backup:trigger"
                or p == "config:diff:view"
                or p == "ai:chat:send"
                or p == "ai:session:create"
                or p == "ai:analysis:view"
                or p == "ai:report:view"
                or p == "knowledge:article:create"
                or p == "knowledge:article:update"
                or p == "knowledge:search:execute"
            )
        },
    },
    "viewer": {
        "name": "只读观察员",
        "description": "仅查看操作",
        "permissions": {
            p for p in ALL_PERMISSIONS
            if p.endswith(":list") or p.endswith(":retrieve") or p.endswith(":view")
            or p == "knowledge:search:execute"
            or p == "ai:chat:send"
            or p == "ai:analysis:view"
            or p == "ai:report:view"
            or p == "ai:knowledgegraph:view"
        },
    },
    "auditor": {
        "name": "审计员",
        "description": "审计和事件只读",
        "permissions": {
            p for p in ALL_PERMISSIONS
            if p.startswith("platform:audit:")
            or p.startswith("eventwall:event:")
            or p.startswith("eventwall:fault:")
            or p == "ai:audit:view"
        },
    },
    "demo": {
        "name": "演示账号",
        "description": "只读 + 变更禁止",
        "permissions": {
            p for p in ALL_PERMISSIONS
            if p.endswith(":list") or p.endswith(":retrieve") or p.endswith(":view")
            or p == "knowledge:search:execute"
        },
    },
}
