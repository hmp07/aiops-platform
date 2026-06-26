"""M6 APM — iTop dependency graph builder.

Traverses iTop CI foreign-key relationships to build a complete
service dependency graph suitable for ReactFlow visualization.
"""
from app.integrations.itop.client import ItopAdapter


CI_TYPE_LABELS: dict[str, str] = {
    "ApplicationSolution": "应用",
    "DatabaseSchema": "数据库Schema",
    "DBServer": "数据库实例",
    "WebServer": "Web服务",
    "WebApplication": "Web应用",
    "VirtualMachine": "虚拟机",
    "Farm": "虚拟化集群",
    "Hypervisor": "宿主机",
    "Server": "物理服务器",
    "NetworkDevice": "网络设备",
    "StorageSystem": "存储系统",
    "Rack": "机柜",
}

# FK rules: (source_class, fk_field, target_class)
_FK_RULES: list[tuple[str, str, str]] = [
    ("DatabaseSchema", "dbserver_id", "DBServer"),
    ("DBServer", "system_id", "Server"),
    ("DBServer", "system_id", "VirtualMachine"),
    ("WebServer", "system_id", "Server"),
    ("WebServer", "system_id", "VirtualMachine"),
    ("WebApplication", "webserver_id", "WebServer"),
    ("Hypervisor", "server_id", "Server"),
]

# List-field rules: (source_class, list_field, target_class, edge_label)
_LIST_RULES: list[tuple[str, str, str, str]] = [
    ("Farm", "hypervisor_list", "Hypervisor", "contains"),
    ("Farm", "virtualmachine_list", "VirtualMachine", "contains"),
    ("WebServer", "webapp_list", "WebApplication", "hosts"),
]

MAX_DEPTH = 8


async def build_dependency_graph(itop: ItopAdapter) -> dict:
    """Build complete dependency graph from iTop data.

    Returns {"nodes": [...], "edges": [...]} for ReactFlow.
    """
    nodes: list[dict] = []
    edges: list[dict] = []
    seen: set[str] = set()
    edge_ids: set[str] = set()
    fci_index: dict[tuple[str, int], dict] = {}
    reverse_index: dict[str, list[tuple[str, int, str]]] = {}

    # ── Phase 1: Load all infrastructure CIs ──
    all_cis = await itop.get_all_functional_cis()
    for ci in all_cis:
        cls = ci.get("ci_class") or ci.get("finalclass", "FunctionalCI")
        ci_id = ci.get("id", 0)
        if ci_id:
            fci_index[(cls, ci_id)] = ci
        _build_reverse(ci, cls, ci_id, reverse_index)

    # ── Phase 2: Load ApplicationSolutions, build initial graph ──
    apps = await itop.get_applications_with_fcis()
    for app in apps:
        app_id = app.get("id", 0)
        app_name = app.get("name", f"App-{app_id}")
        app_key = ("ApplicationSolution", app_id)
        if app_key in seen:
            continue
        seen.add(app_key)
        nodes.append(_make_node("ApplicationSolution", app_id, app_name, app))

        for link in (app.get("functionalcis_list") or []):
            fci_id = int(link.get("functionalci_id", 0))
            fci_name = link.get("functionalci_name", "")
            fci_class = link.get("functionalci_id_finalclass_recall", "")
            if not fci_id or not fci_class:
                continue
            child_key = (fci_class, fci_id)
            if child_key not in seen:
                _add_node(nodes, seen, fci_class, fci_id, fci_name, fci_index)
            _add_edge(edges, edge_ids, f"e-app-{app_id}-fci-{fci_id}",
                      _nid("ApplicationSolution", app_id),
                      _nid(fci_class, fci_id), "depends on")
            _expand(fci_class, fci_id, fci_index, reverse_index,
                    nodes, edges, seen, edge_ids, depth=1)

    return {"nodes": nodes, "edges": edges}


def _expand(ci_class: str, ci_id: int,
            fci_index: dict, reverse_index: dict,
            nodes: list, edges: list, seen: set, edge_ids: set,
            depth: int):
    """BFS expand from a CI node, following FK + list + reverse edges."""
    if depth >= MAX_DEPTH:
        return
    parent_nid = _nid(ci_class, ci_id)
    ci = fci_index.get((ci_class, ci_id), {})

    # 1. Forward scalar FK
    for src, fk, tgt in _FK_RULES:
        if src != ci_class:
            continue
        tgt_id = ci.get(fk, 0)
        if not tgt_id or int(tgt_id) == 0:
            continue
        tgt_id = int(tgt_id)
        tgt_name = ci.get(f"{fk}_name", "") or ci.get(
            fk.replace("_id", "_friendlyname", 1) if "_id" in fk else fk + "_friendlyname", "")
        _link(nodes, edges, seen, edge_ids, fci_index,
              (ci_class, ci_id), parent_nid, (tgt, tgt_id), tgt_name,
              fk.replace("_id", ""), depth, fci_index, reverse_index)

    # 2. Forward list FK
    for src, field, tgt_class, label in _LIST_RULES:
        if src != ci_class:
            continue
        for item in (ci.get(field) or []):
            if not isinstance(item, dict):
                continue
            item_name = item.get("name", "")
            item_id = _resolve_id(item, tgt_class, fci_index)
            if not item_id:
                continue
            _link(nodes, edges, seen, edge_ids, fci_index,
                  (ci_class, ci_id), parent_nid, (tgt_class, item_id), item_name,
                  label, depth, fci_index, reverse_index)

    # 3. Reverse lookup (parent side of 1:N)
    ci_name = ci.get("name", "")
    for lk in [str(ci_id), f"{ci_class}:{ci_name}"]:
        for p_cls, p_id, field in reverse_index.get(lk, []):
            p_nid = _nid(p_cls, p_id)
            if _add_edge(edges, edge_ids, f"e-rev-{p_id}-{ci_id}-{field}",
                         p_nid, parent_nid, field.replace("_list", "")):
                if (p_cls, p_id) not in seen:
                    pci = fci_index.get((p_cls, p_id), {})
                    _add_node(nodes, seen, p_cls, p_id, pci.get("name", ""), fci_index)
                _expand(p_cls, p_id, fci_index, reverse_index,
                        nodes, edges, seen, edge_ids, depth + 1)


def _link(nodes, edges, seen, edge_ids, fci_index,
          parent_key, parent_nid, child_key, child_name, label, depth,
          fci_index2, reverse_index):
    """Add a single node+edge and recurse."""
    cls, cid = child_key
    if child_key not in seen:
        _add_node(nodes, seen, cls, cid, child_name, fci_index)
    child_nid = _nid(cls, cid)
    if _add_edge(edges, edge_ids, f"e-{parent_key[1]}-{cid}-{label}",
                 parent_nid, child_nid, label):
        _expand(cls, cid, fci_index, reverse_index, nodes, edges, seen, edge_ids, depth + 1)


def _resolve_id(item: dict, hint_class: str, fci_index: dict) -> int:
    """Resolve a list item to its CI id (by name or explicit id)."""
    iid = item.get("id", 0)
    if iid:
        return int(iid)
    name = item.get("name", "")
    if not name:
        return 0
    for (cls, cid), ci in fci_index.items():
        if ci.get("name") == name:
            return cid
    return 0


def _build_reverse(ci: dict, cls: str, ci_id: int, rev: dict):
    """Build reverse index from list fields."""
    if not ci_id:
        return
    for field in ci:
        if not field.endswith("_list"):
            continue
        for item in (ci.get(field) or []):
            if not isinstance(item, dict):
                continue
            name = item.get("name", "")
            fid = item.get("id", 0)
            if name:
                rev.setdefault(f"{item.get('finalclass', '')}:{name}", []).append(
                    (cls, ci_id, field))
            if fid:
                rev.setdefault(str(fid), []).append((cls, ci_id, field))


def _add_node(nodes, seen, cls, ci_id, name, fci_index):
    key = (cls, ci_id)
    if key in seen:
        return
    seen.add(key)
    ci = fci_index.get(key, {})
    nodes.append(_make_node(cls, ci_id, name or ci.get("name", f"{cls}-{ci_id}"), ci))


def _make_node(cls, ci_id, name, ci):
    return {
        "id": _nid(cls, ci_id),
        "label": name,
        "type": cls,
        "type_label": CI_TYPE_LABELS.get(cls, cls),
        "properties": {
            "name": name, "status": ci.get("status", ""),
            "org": ci.get("organization_name", ""),
        },
    }


def _add_edge(edges, edge_ids, eid, source, target, label):
    if eid not in edge_ids:
        edge_ids.add(eid)
        edges.append({"id": eid, "source": source, "target": target,
                       "label": label, "type": "dependency"})
        return True
    return False


def _nid(cls: str, ci_id: int) -> str:
    return f"{cls}:{ci_id}"
