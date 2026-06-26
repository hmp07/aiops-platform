"""M8 AIOps — MCP Protocol Endpoints (sxdevops architecture).

JSON-RPC compatible MCP endpoints for platform tool discovery and invocation.
Porting from: sxdevops/backend/aiops/views.py platform_mcp_* functions.
"""

import logging

from fastapi import APIRouter, Body, Depends

from app.core.middleware.auth import get_current_user
from app.modules.module8_aiops import services as aiops_services

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/aiops/mcp", tags=["AIOps MCP"])

MCP_PROTOCOL_VERSION = "2025-03-26"
MCP_CLIENT_INFO = {"name": "AIOps Platform", "version": "1.0.0"}


@router.get("/manifest")
async def platform_mcp_manifest(current_user: dict = Depends(get_current_user)):
    """Return the platform MCP manifest (JSON-RPC compatible).

    Used by MCP clients to discover server capabilities.
    """
    return {
        "protocolVersion": MCP_PROTOCOL_VERSION,
        "serverInfo": MCP_CLIENT_INFO,
        "capabilities": {
            "tools": {"listChanged": False},
        },
    }


@router.get("/tools")
async def platform_mcp_tools(current_user: dict = Depends(get_current_user)):
    """List all available platform MCP tools.

    Returns tools in MCP-compatible format with inputSchema and annotations.
    """
    tools = aiops_services.list_platform_mcp_tools(current_user)
    return {"tools": tools}


@router.post("/call")
async def platform_mcp_call(
    body: dict = Body(...),
    current_user: dict = Depends(get_current_user),
):
    """Invoke a platform MCP tool directly.

    Request body: {"name": "aiops.query_devices", "arguments": {"query": "server", "limit": 5}}
    """
    tool_name = body.get("name", "")
    arguments = body.get("arguments", {})

    if not tool_name:
        return {"error": "tool name required"}

    result = await aiops_services.invoke_platform_mcp_tool(
        tool_name=tool_name,
        arguments=arguments,
        user=current_user,
    )
    return {"result": result}


@router.post("/rpc")
async def platform_mcp_rpc(
    body: dict = Body(...),
    current_user: dict = Depends(get_current_user),
):
    """JSON-RPC endpoint for MCP protocol.

    Supports: initialize, ping, tools/list, tools/call methods.
    """
    method = body.get("method", "")
    req_id = body.get("id")
    params = body.get("params", {})

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": MCP_PROTOCOL_VERSION,
                "serverInfo": MCP_CLIENT_INFO,
                "capabilities": {"tools": {"listChanged": False}},
            },
        }

    if method == "ping":
        return {"jsonrpc": "2.0", "id": req_id, "result": {}}

    if method == "tools/list":
        tools = aiops_services.list_platform_mcp_tools(current_user)
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": tools}}

    if method == "tools/call":
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})
        if not tool_name:
            return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32602, "message": "Missing tool name"}}
        result = await aiops_services.invoke_platform_mcp_tool(
            tool_name=tool_name, arguments=arguments, user=current_user,
        )
        return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": str(result)}]}}

    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {"code": -32601, "message": f"Method not found: {method}"},
    }
