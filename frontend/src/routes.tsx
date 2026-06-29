import { Navigate, RouteObject } from "react-router-dom";
import MainLayout from "./layouts/MainLayout";
import LoginPage from "./pages/LoginPage";
import DashboardPage from "./pages/DashboardPage";
import DeviceListPage from "./pages/asset/DeviceListPage";
import DeviceDetailPage from "./pages/asset/DeviceDetailPage";
import SubnetTreePage from "./pages/ipam/SubnetTreePage";
import AlertListPage from "./pages/monitoring/AlertListPage";
import AlertDetailPage from "./pages/monitoring/AlertDetailPage";
import LogExplorerPage from "./pages/log/LogExplorerPage";
import ConfigBackupPage from "./pages/config/ConfigBackupPage";
import ServiceListPage from "./pages/apm/ServiceListPage";
import TopologyPage from "./pages/apm/TopologyPage";
import KnowledgePage from "./pages/knowledge/KnowledgePage";
import AIChatPage from "./pages/ai/AIChatPage";
import InspectionPage from "./pages/ai/InspectionPage";
import ModelProviderPage from "./pages/ai/ModelProviderPage";
import AIOpsConfigPage from "./pages/ai/AIOpsConfigPage";
import AIOpsAuditPage from "./pages/ai/AIOpsAuditPage";
import UserManagementPage from "./pages/platform/UserManagementPage";
import AuditLogPage from "./pages/platform/AuditLogPage";
import DataSourcePage from "./pages/platform/DataSourcePage";

export const routes: RouteObject[] = [
  { path: "/login", element: <LoginPage /> },
  {
    path: "/",
    element: <MainLayout />,
    children: [
      { index: true, element: <Navigate to="/dashboard" replace /> },
      { path: "dashboard", element: <DashboardPage /> },
      { path: "asset", element: <DeviceListPage /> },
      { path: "asset/:id", element: <DeviceDetailPage /> },
      { path: "ipam", element: <SubnetTreePage /> },
      { path: "monitoring/alerts", element: <AlertListPage /> },
      { path: "monitoring/alerts/:id", element: <AlertDetailPage /> },
      { path: "log/explorer", element: <LogExplorerPage /> },
      { path: "config/backups", element: <ConfigBackupPage /> },
      { path: "apm/services", element: <ServiceListPage /> },
      { path: "apm/topology", element: <TopologyPage /> },
      { path: "knowledge", element: <KnowledgePage /> },
      { path: "ai/chat", element: <AIChatPage /> },
      { path: "ai/inspection", element: <InspectionPage /> },
      { path: "ai/config", element: <AIOpsConfigPage /> },
      { path: "ai/audit", element: <AIOpsAuditPage /> },
      { path: "admin/users", element: <UserManagementPage /> },
      { path: "admin/datasources", element: <DataSourcePage /> },
      { path: "admin/audit", element: <AuditLogPage /> },
    ],
  },
];
