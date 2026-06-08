import { useQuery } from "@tanstack/react-query";
import { Card } from "antd";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { apiRequest } from "../../api/client";

export function AnalyticsPage() {
  const { data } = useQuery({
    queryKey: ["analytics-overview"],
    queryFn: () => apiRequest<{ completion_rate: number; response_rate: number; enps: number | null }>("/analytics/overview")
  });

  const chartData = [
    { name: "Completion", value: data?.completion_rate ?? 0 },
    { name: "Response", value: data?.response_rate ?? 0 },
    { name: "eNPS", value: data?.enps ?? 0 }
  ];

  return (
    <Card title="Analytics">
      <ResponsiveContainer width="100%" height={320}>
        <BarChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" />
          <YAxis />
          <Tooltip />
          <Bar dataKey="value" fill="#1677ff" />
        </BarChart>
      </ResponsiveContainer>
    </Card>
  );
}

