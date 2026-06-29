import { useState } from "react";
import { Outlet, useNavigate, useLocation } from "react-router-dom";
import { Layout, Menu, Avatar, Dropdown, theme } from "antd";
import {
  DashboardOutlined,
  DesktopOutlined,
  ApartmentOutlined,
  AlertOutlined,
  FileSearchOutlined,
  CloudServerOutlined,
  NodeIndexOutlined,
  BookOutlined,
  RobotOutlined,
  SettingOutlined,
  LogoutOutlined,
  UserOutlined,
} from "@ant-design/icons";
import { useAuthStore } from "../stores/useAuthStore";

const { Header, Sider, Content } = Layout;

const menuItems = [
  { key: "/dashboard", icon: <DashboardOutlined />, label: "仪表盘" },
  {
    key: "asset",
    icon: <DesktopOutlined />,
    label: "设备资产",
    children: [
      { key: "/asset", label: "设备列表" },
    ],
  },
  {
    key: "ipam",
    icon: <ApartmentOutlined />,
    label: "IP 管理",
    children: [
      { key: "/ipam", label: "子网管理" },
    ],
  },
  {
    key: "monitoring",
    icon: <AlertOutlined />,
    label: "监控告警",
    children: [
      { key: "/monitoring/alerts", label: "告警列表" },
    ],
  },
  {
    key: "log",
    icon: <FileSearchOutlined />,
    label: "日志分析",
    children: [
      { key: "/log/explorer", label: "日志检索" },
    ],
  },
  {
    key: "config",
    icon: <CloudServerOutlined />,
    label: "配置管理",
    children: [
      { key: "/config/backups", label: "备份管理" },
    ],
  },
  {
    key: "apm",
    icon: <NodeIndexOutlined />,
    label: "应用性能",
    children: [
      { key: "/apm/services", label: "服务列表" },
      { key: "/apm/topology", label: "服务拓扑" },
    ],
  },
  {
    key: "knowledge",
    icon: <BookOutlined />,
    label: "知识库",
    children: [
      { key: "/knowledge", label: "知识库" },
    ],
  },
  {
    key: "ai",
    icon: <RobotOutlined />,
    label: "AI 运维",
    children: [
      { key: "/ai/chat", label: "AI 问答" },
      { key: "/ai/config", label: "智能体配置" },
      { key: "/ai/audit", label: "审计日志" },
      { key: "/ai/inspection", label: "巡检报告" },
    ],
  },
  {
    key: "admin",
    icon: <SettingOutlined />,
    label: "系统管理",
    children: [
      { key: "/admin/datasources", label: "数据源管理" },
      { key: "/admin/users", label: "用户管理" },
      { key: "/admin/audit", label: "审计日志" },
    ],
  },
];

export default function MainLayout() {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuthStore();
  const { token: themeToken } = theme.useToken();

  const handleMenuClick = ({ key }: { key: string }) => {
    navigate(key);
  };

  const userMenu = {
    items: [
      { key: "profile", icon: <UserOutlined />, label: "个人信息" },
      { type: "divider" as const },
      { key: "logout", icon: <LogoutOutlined />, label: "退出登录", danger: true },
    ],
    onClick: ({ key }: { key: string }) => {
      if (key === "logout") {
        logout();
        navigate("/login");
      }
    },
  };

  const selectedKey = menuItems
    .flatMap((item) => (item.children ? item.children : [item]))
    .find((item) => item.key === location.pathname || location.pathname.startsWith(item.key + "/"));

  const openKeys = menuItems
    .filter((item) => item.children?.some((child) =>
      location.pathname.startsWith(child.key)
    ))
    .map((item) => item.key);

  return (
    <Layout style={{ minHeight: "100vh" }}>
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        theme="dark"
        width={220}
      >
        <div style={{
          height: 64,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          color: "#fff",
          fontSize: collapsed ? 16 : 18,
          fontWeight: 700,
          borderBottom: "1px solid rgba(255,255,255,0.1)",
        }}>
          {collapsed ? "AO" : "AIOps Platform"}
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={selectedKey ? [selectedKey.key] : []}
          defaultOpenKeys={openKeys}
          items={menuItems}
          onClick={handleMenuClick}
        />
      </Sider>
      <Layout>
        <Header style={{ background: themeToken.colorBgContainer, padding: "0 24px", display: "flex", justifyContent: "flex-end", alignItems: "center", borderBottom: "1px solid #f0f0f0" }}>
          <Dropdown menu={userMenu}>
            <div style={{ cursor: "pointer", display: "flex", alignItems: "center", gap: 8 }}>
              <Avatar icon={<UserOutlined />} />
              <span>{user?.display_name || "未登录"}</span>
            </div>
          </Dropdown>
        </Header>
        <Content style={{ margin: 24, minHeight: 280 }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
}
