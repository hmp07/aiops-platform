import client from "./client";

// M1: Device Asset
export const deviceApi = {
  list: (params?: any) => client.get("/devices", { params }),
  create: (data: any) => client.post("/devices", data),
  get: (id: string) => client.get(`/devices/${id}`),
  update: (id: string, data: any) => client.post(`/devices/${id}/update`, data),
  delete: (id: string) => client.post(`/devices/${id}/delete`),
};

// Device Metrics (Zabbix real-time monitoring)
export const metricsApi = {
  getDeviceMetrics: (deviceId: string) => client.post(`/devices/${deviceId}/metrics`),
  getDeviceAlerts: (deviceId: string, params?: any) => client.get(`/devices/${deviceId}/alerts`, { params }),
};

// M2: IPAM
export const ipamApi = {
  listSubnets: (params?: any) => client.get("/ipam/subnets", { params }),
  createSubnet: (data: any) => client.post("/ipam/subnets", data),
  listAllocations: (params?: any) => client.get("/ipam/allocations", { params }),
  allocate: (data: any) => client.post("/ipam/allocations/allocate", data),
  release: (id: string) => client.post(`/ipam/allocations/${id}/release`),
};

// M3: Alerts
export const alertApi = {
  list: (params?: any) => client.get("/alerts", { params }),
  get: (id: string) => client.get(`/alerts/${id}`),
  stats: () => client.get("/alerts/stats"),
  acknowledge: (id: string) => client.post(`/alerts/${id}/acknowledge`),
  resolve: (id: string) => client.post(`/alerts/${id}/resolve`),
  close: (id: string) => client.post(`/alerts/${id}/close`),
};

// M4: Logs
export const logApi = {
  list: (params?: any) => client.get("/logs/entries", { params }),
  ingest: (data: any) => client.post("/logs/ingest", data),
  listSources: () => client.get("/logs/sources"),
};

// M5: Config
export const configApi = {
  listBackups: (params?: any) => client.get("/configs/backups", { params }),
  triggerBackup: (data?: any) => client.post("/configs/backups/trigger", data || {}),
  getDiff: (deviceId: string) => client.get(`/configs/diff/${deviceId}`),
  listDiffs: (params?: any) => client.get("/configs/diffs", { params }),
};

// M6: APM
export const apmApi = {
  listServices: (params?: any) => client.get("/apm/services", { params }),
  createService: (data: any) => client.post("/apm/services", data),
  getTopology: () => client.get("/apm/topology"),
  addEdge: (data: any) => client.post("/apm/topology/edges", data),
  getCrossLayer: (serviceId: string) => client.get(`/apm/cross-layer/${serviceId}`),
};

// M7: Knowledge
export const knowledgeApi = {
  listArticles: (params?: any) => client.get("/knowledge/articles", { params }),
  createArticle: (data: any) => client.post("/knowledge/articles", data),
  search: (data: any) => client.post("/knowledge/search", data),
};

// M8: AI
export const aiApi = {
  listSessions: () => client.get("/ai/sessions"),
  createSession: (data?: any) => client.post("/ai/sessions", data || {}),
  getSuggestions: (page: string) => client.get(`/ai/suggestions?page=${page}`),
  listSkills: () => client.get("/ai/skills"),
};

// M9: Platform
export const platformApi = {
  listUsers: (params?: any) => client.get("/auth/users", { params }),
  listAudit: (params?: any) => client.get("/auth/audit", { params }),
  getPermissions: () => client.get("/auth/permissions"),
};
