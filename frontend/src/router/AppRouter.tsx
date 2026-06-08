import { BarChartOutlined, BellOutlined, FormOutlined, HomeOutlined, LogoutOutlined } from "@ant-design/icons";
import { Button, Layout, Menu } from "antd";
import { BrowserRouter, Link, Navigate, Route, Routes, useNavigate } from "react-router-dom";
import { LoginPage } from "../pages/LoginPage";
import { AnalyticsPage } from "../pages/hr/AnalyticsPage";
import { HrDashboardPage } from "../pages/hr/HrDashboardPage";
import { SurveyBuilderPage } from "../pages/hr/SurveyBuilderPage";
import { SurveyManagementPage } from "../pages/hr/SurveyManagementPage";
import { EmployeeDashboardPage } from "../pages/employee/EmployeeDashboardPage";
import { NotificationSettingsPage } from "../pages/employee/NotificationSettingsPage";
import { SurveyListPage } from "../pages/employee/SurveyListPage";
import { SurveyPassPage } from "../pages/employee/SurveyPassPage";
import { useAuthStore } from "../stores/authStore";

function Shell() {
  const navigate = useNavigate();
  const { accessToken, logout } = useAuthStore();

  if (!accessToken) {
    return <Navigate to="/login" replace />;
  }

  return (
    <Layout className="app-shell">
      <Layout.Sider width={240}>
        <Menu
          theme="dark"
          mode="inline"
          defaultSelectedKeys={["employee-dashboard"]}
          items={[
            { key: "employee-dashboard", icon: <HomeOutlined />, label: <Link to="/employee">Dashboard</Link> },
            { key: "employee-surveys", icon: <FormOutlined />, label: <Link to="/employee/surveys">Surveys</Link> },
            { key: "notifications", icon: <BellOutlined />, label: <Link to="/notifications">Notifications</Link> },
            { key: "hr-dashboard", icon: <BarChartOutlined />, label: <Link to="/hr">HR Dashboard</Link> },
            { key: "hr-surveys", icon: <FormOutlined />, label: <Link to="/hr/surveys">Survey Management</Link> },
            { key: "analytics", icon: <BarChartOutlined />, label: <Link to="/hr/analytics">Analytics</Link> }
          ]}
        />
      </Layout.Sider>
      <Layout>
        <Layout.Header style={{ display: "flex", justifyContent: "flex-end", background: "#fff" }}>
          <Button
            icon={<LogoutOutlined />}
            onClick={() => {
              logout();
              navigate("/login");
            }}
          />
        </Layout.Header>
        <Layout.Content className="content">
          <Routes>
            <Route path="/employee" element={<EmployeeDashboardPage />} />
            <Route path="/employee/surveys" element={<SurveyListPage />} />
            <Route path="/employee/surveys/:surveyId" element={<SurveyPassPage />} />
            <Route path="/notifications" element={<NotificationSettingsPage />} />
            <Route path="/hr" element={<HrDashboardPage />} />
            <Route path="/hr/surveys" element={<SurveyManagementPage />} />
            <Route path="/hr/surveys/:surveyId/builder" element={<SurveyBuilderPage />} />
            <Route path="/hr/analytics" element={<AnalyticsPage />} />
            <Route path="*" element={<Navigate to="/employee" replace />} />
          </Routes>
        </Layout.Content>
      </Layout>
    </Layout>
  );
}

export function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/*" element={<Shell />} />
      </Routes>
    </BrowserRouter>
  );
}

