/** AIOps API client — mirrors sxdevops frontend/src/api/modules/aiops.js */
import client from "./client";

const AIOPS_CHAT_TIMEOUT = 120000;

// Bootstrap
export const getBootstrap = () => client.get("/aiops/bootstrap");

// Sessions
export const getSessions = (params?: any) => client.get("/aiops/sessions", { params });
export const createSession = (data: any) => client.post("/aiops/sessions", data);
export const deleteSession = (id: string) => client.post(`/aiops/sessions/${id}/delete_session`);

// Messages
export const getMessages = (id: string) => client.get(`/aiops/sessions/${id}/messages`);
export const sendMessageAsync = (id: string, data: any) =>
  client.post(`/aiops/sessions/${id}/send_message_async`, data);
export const executePending = (id: string) =>
  client.post(`/aiops/sessions/${id}/execute_pending`, {}, { timeout: AIOPS_CHAT_TIMEOUT });

// Actions
export const confirmAction = (id: string) => client.post(`/aiops/actions/${id}/confirm`);
export const cancelAction = (id: string) => client.post(`/aiops/actions/${id}/cancel`);

// Knowledge Graph
export const getKnowledgeGraph = (params?: any) => client.get("/aiops/knowledge-graph", { params });

// Admin: Config
export const getConfig = () => client.get("/aiops/admin/config");
export const updateConfig = (data: any) => client.put("/aiops/admin/config", data);

// Admin: Providers
export const getProviders = () => client.get("/aiops/admin/providers");
export const getProviderPresets = () => client.get("/aiops/admin/providers/presets");
export const createProvider = (data: any) => client.post("/aiops/admin/providers", data);
export const testProvider = (id: string) => client.post(`/aiops/admin/providers/${id}/test_connection`);
export const listProviderModels = (id: string) => client.get(`/aiops/admin/providers/${id}/models`);
export const deleteProvider = (id: string) => client.post(`/aiops/admin/providers/${id}/delete`);

// Admin: MCP Servers
export const getMcpServers = () => client.get("/aiops/admin/mcp-servers");
export const createMcpServer = (data: any) => client.post("/aiops/admin/mcp-servers", data);
export const updateMcpServer = (id: string, data: any) => client.patch(`/aiops/admin/mcp-servers/${id}`, data);
export const deleteMcpServer = (id: string) => client.delete(`/aiops/admin/mcp-servers/${id}`);
export const testMcpServer = (id: string) => client.post(`/aiops/admin/mcp-servers/${id}/test_connection`);
export const listMcpTools = (id: string) => client.get(`/aiops/admin/mcp-servers/${id}/list_tools`);

// Admin: Skills
export const getSkills = () => client.get("/aiops/admin/skills");
export const createSkill = (data: any) => client.post("/aiops/admin/skills", data);
export const updateSkill = (id: string, data: any) => client.patch(`/aiops/admin/skills/${id}`, data);
export const deleteSkill = (id: string) => client.delete(`/aiops/admin/skills/${id}`);
export const getSkillMarketplace = () => client.get("/aiops/admin/skills/marketplace");
export const cloneSkill = (id: string, data?: any) => client.post(`/aiops/admin/skills/${id}/clone`, data || {});

// Admin: Actions
export const getActions = () => client.get("/aiops/admin/actions");
export const preflightAction = (data: any) => client.post("/aiops/admin/actions/preflight", data);

// Admin: Audit
export const getAuditOverview = (params?: any) => client.get("/aiops/admin/audit/overview", { params });
export const getAuditCosts = (params?: any) => client.get("/aiops/admin/audit/costs", { params });
export const getAuditSessions = (params?: any) => client.get("/aiops/admin/audit/sessions", { params });
export const deleteAuditSession = (id: string) => client.delete(`/aiops/admin/audit/sessions/${id}`);
export const getAuditToolInvocations = (params?: any) => client.get("/aiops/admin/audit/tool-invocations", { params });
export const getAuditModelInvocations = (params?: any) => client.get("/aiops/admin/audit/model-invocations", { params });
export const getAuditActions = (params?: any) => client.get("/aiops/admin/audit/actions", { params });

// MCP Protocol
export const getMcpManifest = () => client.get("/aiops/mcp/manifest");
export const getMcpTools = () => client.get("/aiops/mcp/tools");
export const callMcpTool = (data: any) => client.post("/aiops/mcp/call", data);
