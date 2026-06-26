# iTop REST JSON API 参考手册

> 涵盖 iTop 核心 + TeemIp IPAM 扩展，基于实际对接验证（iTop 3.x + TeemIp 1.2）

## 1. 基础概念

### 1.1 请求方式

```
POST http://{itop-host}/webservices/rest.php
Content-Type: application/x-www-form-urlencoded
```

**所有请求都是 POST**，参数以表单字段形式提交（不是 JSON body）。

### 1.2 认证

认证信息**嵌入在 POST 表单字段中**（不是 HTTP Basic Auth Header）：

| 表单字段 | 说明 |
|---------|------|
| `version` | API 版本，推荐 `1.4`（支持分页） |
| `auth_user` | 用户名 |
| `auth_pwd` | 密码 |
| `json_data` | JSON 格式的操作请求体（见下文） |

**Python 示例**：

```python
import requests

def itop_call(url, username, password, payload):
    """通用 iTop REST API 调用"""
    form = {
        "version": "1.4",
        "auth_user": username,
        "auth_pwd": password,
        "json_data": json.dumps(payload),
    }
    resp = requests.post(f"{url}/webservices/rest.php", data=form, timeout=30)
    data = resp.json()
    if data.get("code") != 0:
        raise RuntimeError(f"iTop error {data['code']}: {data.get('message')}")
    return data
```

**注意**：
- 用户必须具有 iTop 的 **REST Services User** 配置文件权限
- 密码中如含 `&` 等特殊字符会被正确编码（用 `requests` 库的 `data=` 参数自动处理）
- iTop 也支持 HTTP Basic Auth，但实际测试中**表单字段方式更可靠**

### 1.3 json_data 结构

每个请求的 `json_data` 是一个 JSON 对象，包含以下通用字段：

```json
{
  "operation": "core/get",       // 操作名（必填）
  "class": "Server",             // 目标类（大多数操作需要）
  "key": "SELECT Server",        // 对象标识：数字ID / OQL查询 / 关联数组
  "output_fields": "id,name",    // 返回字段：逗号分隔 / "*" 全部 / "*+" 含子类
  "fields": { ... },             // 要写入的字段（create/update 时使用）
  "comment": "",                 // 变更日志注释
  "limit": 100,                  // 分页大小（API 1.4+）
  "page": 1                      // 页码（API 1.4+）
}
```

### 1.4 响应格式

```json
{
  "code": 0,                     // 0=成功，其他=错误
  "message": "Found: 5",
  "objects": {
    "Server::42": {
      "code": 0,
      "message": "",
      "class": "Server",
      "key": 42,
      "fields": {
        "id": 42,
        "name": "MyServer",
        "status": "production",
        ...
      }
    }
  }
}
```

**关键点**：`objects` 是一个**字典**（key 为 `"Class::ID"`），不是数组。

| 错误码 | 含义 |
|--------|------|
| 0 | 成功 |
| 1 | 未授权 |
| 2 | 缺少 version 参数 |
| 3 | 缺少 json_data |
| 10 | 不支持的 API 版本 |
| 11 | 未知操作 |
| 12 | 操作不安全 |
| 100 | 内部错误 |

---

## 2. 核心操作（core/*）

### 2.1 列出可用操作

```python
payload = {"operation": "list_operations"}
result = itop_call(url, user, pwd, payload)
for op in result["operations"]:
    print(op["verb"], "-", op["description"])
```

TeemIp 安装后会额外出现 `teemip/*` 操作。

### 2.2 查询对象（core/get）

**最常用的操作**。用 OQL（Object Query Language）查询。

```python
# 查询所有 Server，返回全部字段，每页 100 条
payload = {
    "operation": "core/get",
    "class": "Server",
    "key": "SELECT Server",
    "output_fields": "*",
    "limit": 100,
}
result = itop_call(url, user, pwd, payload)
# result["objects"] 是 {"Server::1": {...}, "Server::2": {...}, ...}
```

**OQL 查询示例**：

```python
# 过滤：只查生产状态的 Server
"key": "SELECT Server WHERE status = 'production'"

# 只返回指定字段
"key": "SELECT Server",
"output_fields": "id,name,status,org_id"

# 分页
"limit": 50, "page": 1

# 按条件查询 NetworkDevice
"key": "SELECT NetworkDevice WHERE brand_id = 11"
```

**解析响应的标准方法**（objects dict → flat list）：

```python
def parse_objects(result, ci_class):
    objects = result.get("objects") or {}
    if not isinstance(objects, dict):
        return []
    return [
        {**v.get("fields", {}), "ci_class": ci_class,
         "id": int(v.get("key", 0))}
        for v in objects.values()
    ]
```

### 2.3 创建对象（core/create）

```python
payload = {
    "operation": "core/create",
    "class": "Server",
    "comment": "通过 REST API 创建",
    "output_fields": "id,name",
    "fields": {
        "name": "NewServer",
        "org_id": 3,
        "status": "production",
        "brand_id": 11,
        "model_id": 13,
    },
}
result = itop_call(url, user, pwd, payload)
# 返回的 objects 中包含新创建的对象 ID
```

### 2.4 更新对象（core/update）

```python
payload = {
    "operation": "core/update",
    "class": "Server",
    "key": 42,                    # 数字 ID
    "fields": {
        "serialnumber": "ABC123456",
        "description": "Updated via API",
    },
}
result = itop_call(url, user, pwd, payload)
```

**注意**：不支持批量更新，`key` 必须精确匹配单个对象。更新只发送需要修改的字段，未指定的字段保持不变。

### 2.5 删除对象（core/delete）

```python
payload = {
    "operation": "core/delete",
    "class": "Server",
    "key": 12788,
}
# 模拟删除（不实际删除）
payload["simulate"] = True
```

---

## 3. 主要 CI 类及其字段

### 3.1 Server

```
字段: name, description, org_id, organization_name, business_criticity,
      status, brand_id, brand_name, model_id, model_name,
      serialnumber, asset_number, purchase_date, end_of_warranty,
      location_id, location_name, rack_id, rack_name,
      managementip_id, managementip_name,
      osfamily_id, osfamily_name, osversion_id, osversion_name,
      oslicence_id, oslicence_name,
      cpu, ram, nb_u,
      finalclass, friendlyname
```

### 3.2 NetworkDevice

```
字段: name, org_id, organization_name, business_criticity,
      status, brand_id, brand_name, model_id, model_name,
      location_id, location_name, rack_id,
      networkdevicetype_id, networkdevicetype_name (Router/Switch/...),
      managementip_id, managementip_name,
      iosversion_id, iosversion_name,
      serialnumber, asset_number,
      finalclass, friendlyname
```

### 3.3 VirtualMachine

```
字段: name, org_id, organization_name,
      status, virtualizationhost_id,
      osfamily_id, osfamily_name, osversion_id, osversion_name,
      cpu, ram,
      managementip_id, managementip_name,
      finalclass, friendlyname
```

### 3.4 StorageSystem

```
字段: name, org_id, organization_name,
      status, brand_id, brand_name, model_id, model_name,
      location_id, location_name,
      managementip_id, managementip_name,
      serialnumber,
      finalclass, friendlyname
```

### 3.5 其他 CI 类

| 类名 | 说明 |
|------|------|
| `PC` | 个人电脑 |
| `Printer` | 打印机 |
| `ApplicationSolution` | 应用系统 |
| `Brand` | 品牌 |
| `Model` | 型号 |
| `Organization` | 组织 |
| `Location` | 位置 |

---

## 4. TeemIp IPAM 扩展

TeemIp 在标准 iTop REST API 基础上增加了 IP 地址管理专用的操作和 CI 类。

### 4.1 TeemIp Web Services 版本

```python
payload = {"operation": "teemip/get_webservices_version"}
# 返回: "TeemIp WEB Services version running is: 1.2"
```

### 4.2 IPv4Subnet（子网）

**查询子网**：

```python
# 获取所有 IPv4 子网
payload = {
    "operation": "core/get",
    "class": "IPv4Subnet",
    "key": "SELECT IPv4Subnet",
    "output_fields": "*",
    "limit": 200,
}

# 按组织过滤
payload["key"] = "SELECT IPv4Subnet WHERE org_id = 3"
```

**返回字段**：`name`, `ip`, `mask`, `org_id`, `org_name`, `status`, `description`, `type`, `vrfs`, `gateway_ip`

**掩码转换**（dotted → CIDR prefix）：

```python
def mask_to_prefix(mask):
    """255.255.254.0 → 23"""
    return sum(bin(int(o)).count("1") for o in mask.split("."))

# 构建 CIDR: f"{ip}/{mask_to_prefix('255.255.254.0')}" → "10.128.0.0/23"
```

### 4.3 IPv4Address（IP 地址）

```python
payload = {
    "operation": "core/get",
    "class": "IPv4Address",
    "key": "SELECT IPv4Address",
    "output_fields": "*",
    "limit": 500,
}

# 按子网过滤
payload["key"] = "SELECT IPv4Address WHERE subnet_id = 8"
```

**返回字段**：`ip`, `short_name`, `status` (allocated/released/reserved/unassigned), `subnet_id`, `domain_id`, `domain_name`, `requestor_id`, `fqdn`

### 4.4 IPv4Block（IP 地址块）

```python
payload = {
    "operation": "core/get",
    "class": "IPv4Block",
    "key": "SELECT IPv4Block",
    "output_fields": "*",
}
```

**返回字段**：`name`, `ip`, `mask`, `org_id`, `status`, `type`

### 4.5 IPv6Subnet / IPv6Address / IPv6Block

与 IPv4 对应类用法完全相同，将类名中的 `4` 替换为 `6` 即可。

### 4.6 子网 IP 使用统计（TeemIp 专属）

**`teemip/get_nb_of_registered_ips_in_subnet`** —— 获取每个子网的 IP 使用详情：

```python
payload = {
    "operation": "teemip/get_nb_of_registered_ips_in_subnet",
    "class": "IPv4Subnet",
    "key": "SELECT IPv4Subnet",          # 单子网: {"org_id": 3, "ip": "10.129.2.0"}
}
result = itop_call(url, user, pwd, payload)

for key, data in result["objects"].items():
    fields = data["fields"]              # org_name, name, ip, mask
    size = data["subnet_size"]           # 子网总大小
    stats = data["nb_of_ips"]            # 使用统计
    print(f"{fields['name']}: {stats['total registered']}/{size} "
          f"(allocated={stats['allocated']}, free={stats['free ips']})")
```

**返回的 stats 字段**：

| 字段 | 说明 |
|------|------|
| `allocated` | 已分配 |
| `released` | 已释放 |
| `reserved` | 已预留 |
| `unassigned` | 未分配 |
| `total registered` | 已注册总数 |
| `free ips` | 空闲可用 |

### 4.7 自动分配 IP（TeemIp 专属）

```python
# 在指定子网中自动选取一个可用 IP
payload = {
    "operation": "teemip/pick_ip_address_in_subnet",
    "class": "IPv4Subnet",
    "key": {"org_id": 3, "ip": "10.129.2.0"},
    "fields": {
        "status": "reserved",
        "short_name": "my-test-ip",
        "comment": "通过 API 自动分配",
    },
    "output_fields": "ip, short_name, domain_name, status",
}
```

### 4.8 在 IP 范围内分配 / 在 Block 中分配子网

```python
# 在指定 IP Range 中自动选取 IP
payload = {
    "operation": "teemip/pick_ip_address_in_range",
    "class": "IPv4Range",
    "key": 22,
    "fields": {"status": "reserved", "short_name": "my-ip"},
    "output_fields": "ip, status",
}

# 在指定 IP Block 中自动划分子网
payload = {
    "operation": "teemip/pick_subnet_in_block",
    "class": "IPv4Block",
    "key": 15,
    "fields": {"name": "New-VLAN", "mask": "24", "status": "reserved"},
    "output_fields": "name, ip, mask, status",
}
```

### 4.9 DNS Zone 文件

```python
payload = {
    "operation": "teemip/get_zone_file",
    "class": "Zone",
    "key": {"org_id": 3, "name": "demo.com."},
    "format": "sort_by_record",
}
# 返回 BIND 格式的 DNS zone 文件文本
```

---

## 5. Python 完整示例

### 5.1 连接测试

```python
import requests, json

URL = "http://192.168.1.248/webservices/rest.php"
USER, PWD = "api_user", "YNqt&2026"

def itop(payload):
    r = requests.post(URL, data={
        "version": "1.4",
        "auth_user": USER,
        "auth_pwd": PWD,
        "json_data": json.dumps(payload),
    }, timeout=30)
    r.raise_for_status()
    d = r.json()
    assert d["code"] == 0, f"Error {d['code']}: {d.get('message')}"
    return d

# 测试连接
r = itop({"operation": "list_operations"})
print("Operations:", len(r["operations"]))
```

### 5.2 获取所有 CI 数据

```python
def get_all(class_name, limit=200):
    result = itop({
        "operation": "core/get",
        "class": class_name,
        "key": f"SELECT {class_name}",
        "output_fields": "*",
        "limit": limit,
    })
    objects = result.get("objects") or {}
    return [
        {**v["fields"], "id": int(v["key"])}
        for v in objects.values()
    ]

servers = get_all("Server")
for s in servers:
    print(f"Server: {s['name']} | {s.get('brand_name')} {s.get('model_name')} | {s['status']}")
```

### 5.3 获取 IPAM 数据

```python
# 子网列表 + 使用统计
subnets = get_all("IPv4Subnet")
stats = itop({
    "operation": "teemip/get_nb_of_registered_ips_in_subnet",
    "class": "IPv4Subnet",
    "key": "SELECT IPv4Subnet",
})
for s in stats.get("objects", {}).values():
    f = s["fields"]
    n = s["nb_of_ips"]
    print(f"  {f['name']}: {f['ip']}/{f['mask']} → {n['total registered']}/{s['subnet_size']} used")

# IP 地址列表
ips = get_all("IPv4Address")
for a in ips:
    print(f"  {a['ip']}: {a.get('short_name','')} ({a['status']})")
```

### 5.4 创建和更新

```python
# 创建子网
r = itop({
    "operation": "core/create",
    "class": "IPv4Subnet",
    "output_fields": "id,name,ip",
    "fields": {
        "name": "New-Subnet",
        "org_id": 3,
        "ip": "10.200.0.0",
        "mask": "255.255.255.0",
        "status": "active",
    },
})

# 更新 Server 的序列号
r = itop({
    "operation": "core/update",
    "class": "Server",
    "key": 1,
    "fields": {"serialnumber": "SN-2024-001"},
})
```

---

## 6. 注意事项

1. **OQL 中的 LIMIT**：iTop 不原生支持 OQL 中的 `LIMIT` 关键字，应使用 `json_data` 中的 `limit` 和 `page` 参数分页
2. **密码特殊字符**：如密码含 `&`，使用 `requests.post(data=form)` 自动编码，不要手动拼接 URL
3. **output_fields = "*"** ：返回当前类的所有字段；`"*+"` 额外返回子类字段
4. **HTTP Basic Auth 与表单字段认证**：两者都支持，但表单字段方式更稳定（本项目已验证）
5. **REST Services User 权限**：确保 iTop 用户具有该 Profile，否则所有请求返回 `code: 1`（未授权）
6. **TeemIp 版本**：可通过 `teemip/get_webservices_version` 检查，不同版本支持的操作可能不同
7. **响应 objects 是字典**：key 格式为 `"ClassName::NumericID"`，不是数组，解析时需注意
