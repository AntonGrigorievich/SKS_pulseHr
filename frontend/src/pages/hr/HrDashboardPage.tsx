import { useQuery } from "@tanstack/react-query";
import { Card, Statistic } from "antd";
import { apiRequest } from "../../api/client";

export function HrDashboardPage() {
  const { data } = useQuery({
    queryKey: ["analytics-overview"],
    queryFn: () =>
      apiRequest<{
        active_surveys: number;
        completion_rate: number;
        response_rate: number;
        enps: number | null;
        notification_efficiency: Record<string, unknown>;
      }>("/analytics/overview")
  });

  return (
    <div className="grid">
      <Card><Statistic title="Active surveys" value={data?.active_surveys ?? 0} /></Card>
      <Card><Statistic title="Completion rate" value={data?.completion_rate ?? 0} suffix="%" /></Card>
      <Card><Statistic title="Response rate" value={data?.response_rate ?? 0} suffix="%" /></Card>
      <Card><Statistic title="eNPS" value={data?.enps ?? 0} /></Card>
    </div>
  );
}

