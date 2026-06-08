import { useQuery } from "@tanstack/react-query";
import { Card, Progress, Statistic } from "antd";
import { apiRequest } from "../../api/client";

export function EmployeeDashboardPage() {
  const { data } = useQuery({
    queryKey: ["employee-dashboard"],
    queryFn: () => apiRequest<{ active_surveys: number; completed_surveys: number; completion_percent: number }>("/employee/dashboard")
  });

  return (
    <div className="grid">
      <Card><Statistic title="Active surveys" value={data?.active_surveys ?? 0} /></Card>
      <Card><Statistic title="Completed surveys" value={data?.completed_surveys ?? 0} /></Card>
      <Card><Progress type="dashboard" percent={data?.completion_percent ?? 0} /></Card>
    </div>
  );
}

