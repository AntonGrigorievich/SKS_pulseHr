import { useQuery } from "@tanstack/react-query";
import { Card, Statistic, Table, Tag } from "antd";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { apiRequest } from "../../api/client";

type DeliveryStats = {
  sent: number;
  failed: number;
  pending: number;
};

type LatestResponse = {
  response_id: string;
  survey_id: string;
  survey_title: string;
  submitted_at: string;
  anonymous: boolean;
};

type AnalyticsOverview = {
  active_surveys: number;
  completion_rate: number;
  response_rate: number;
  enps: number | null;
  latest_responses: LatestResponse[];
  notification_efficiency: Record<string, DeliveryStats>;
};

function formatDate(value: string) {
  return new Date(value).toLocaleString();
}

export function AnalyticsPage() {
  const { data } = useQuery({
    queryKey: ["analytics-overview"],
    queryFn: () => apiRequest<AnalyticsOverview>("/analytics/overview")
  });

  const chartData = [
    { name: "Completion", value: data?.completion_rate ?? 0 },
    { name: "Response", value: data?.response_rate ?? 0 },
    { name: "eNPS", value: data?.enps ?? 0 }
  ];
  const latestResponses = data?.latest_responses ?? [];
  const notificationData = Object.entries(data?.notification_efficiency ?? {}).map(([channel, stats]) => ({
    channel,
    ...stats
  }));

  return (
    <>
      <div className="grid analytics-stat-grid">
        <Card><Statistic title="Active surveys" value={data?.active_surveys ?? 0} /></Card>
        <Card><Statistic title="Completion rate" value={data?.completion_rate ?? 0} suffix="%" /></Card>
        <Card><Statistic title="Response rate" value={data?.response_rate ?? 0} suffix="%" /></Card>
        <Card><Statistic title="eNPS" value={data?.enps ?? "N/A"} /></Card>
      </div>

      <div className="analytics-layout">
        <Card title="Rates">
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

        <Card title="Notification delivery">
          <Table
            size="small"
            rowKey="channel"
            pagination={false}
            dataSource={notificationData}
            columns={[
              { title: "Channel", dataIndex: "channel" },
              { title: "Sent", dataIndex: "sent" },
              { title: "Failed", dataIndex: "failed" },
              { title: "Pending", dataIndex: "pending" }
            ]}
          />
        </Card>
      </div>

      <Card title="Latest responses" style={{ marginTop: 16 }}>
        <Table
          rowKey="response_id"
          dataSource={latestResponses}
          pagination={{ pageSize: 5 }}
          columns={[
            { title: "Survey", dataIndex: "survey_title" },
            { title: "Submitted", dataIndex: "submitted_at", render: (value: string) => formatDate(value) },
            {
              title: "Identity",
              dataIndex: "anonymous",
              render: (anonymous: boolean) => (anonymous ? <Tag color="green">Anonymous</Tag> : <Tag>Named</Tag>)
            }
          ]}
        />
      </Card>
    </>
  );
}
