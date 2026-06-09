import { useQuery } from "@tanstack/react-query";
import type { ColumnsType } from "antd/es/table";
import { Card, Empty, Select, Space, Statistic, Table, Tabs, Tag, Typography } from "antd";
import { useMemo } from "react";
import { useSearchParams } from "react-router-dom";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { apiRequest } from "../../api/client";
import type { QuestionType, Survey } from "../../api/types";

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

type MetricPoint = {
  label: string;
  value: number;
};

type TimelinePoint = {
  date: string;
  responses: number;
};

type ChoiceAnalytics = {
  label: string;
  value: string;
  count: number;
  percent: number;
};

type MatrixRowAnalytics = {
  row: string;
  choice_counts: ChoiceAnalytics[];
};

type QuestionAnalyticsSummary = {
  question_id: string;
  title: string;
  type: QuestionType;
  position: number;
  answer_count: number;
  skipped_count: number;
  choice_counts: ChoiceAnalytics[];
  rating_average: number | null;
  rating_min: number | null;
  rating_max: number | null;
  rating_distribution: ChoiceAnalytics[];
  matrix_rows: MatrixRowAnalytics[];
  text_answers: string[];
};

type RespondentAnalytics = {
  anonymous: boolean;
  label: string;
  user_id: string | null;
  full_name: string | null;
  phone: string | null;
  department: string | null;
  position: string | null;
};

type AnswerAnalytics = {
  question_id: string;
  question_title: string;
  question_type: QuestionType;
  value: Record<string, unknown>;
  display_value: string;
};

type SurveyResponseAnalytics = {
  response_id: string;
  status: string;
  started_at: string;
  submitted_at: string | null;
  respondent: RespondentAnalytics;
  answers: AnswerAnalytics[];
};

type SurveyAnalytics = {
  survey_id: string;
  title: string;
  is_anonymous: boolean;
  assigned_count: number;
  submitted_count: number;
  response_count: number;
  completion_rate: number;
  response_rate: number;
  enps: number | null;
  department_analytics: MetricPoint[];
  timeline: TimelinePoint[];
  question_summaries: QuestionAnalyticsSummary[];
  responses: SurveyResponseAnalytics[];
};

type ResponseTableRow = SurveyResponseAnalytics & {
  answerMap: Record<string, string>;
};

function formatDate(value?: string | null) {
  if (!value) return "Not submitted";
  return new Date(value).toLocaleString();
}

function renderChoiceCounts(choices: ChoiceAnalytics[]) {
  if (!choices.length) return <Typography.Text type="secondary">No answers</Typography.Text>;

  return (
    <div className="answer-summary-list">
      {choices.map((choice) => (
        <span className="answer-summary-item" key={choice.value}>
          <span>{choice.label}</span>
          <strong>{choice.count}</strong>
          <Typography.Text type="secondary">{choice.percent}%</Typography.Text>
        </span>
      ))}
    </div>
  );
}

function renderQuestionSummary(question: QuestionAnalyticsSummary) {
  if (question.type === "RATING") {
    if (question.rating_average === null) return <Typography.Text type="secondary">No answers</Typography.Text>;
    return (
      <Space direction="vertical" size={6}>
        <Space wrap>
          <Tag color="blue">Avg {question.rating_average}</Tag>
          <Tag>Min {question.rating_min}</Tag>
          <Tag>Max {question.rating_max}</Tag>
        </Space>
        {renderChoiceCounts(question.rating_distribution)}
      </Space>
    );
  }

  if (question.type === "MATRIX") {
    if (!question.matrix_rows.length) return <Typography.Text type="secondary">No answers</Typography.Text>;
    return (
      <Space direction="vertical" size={8} className="matrix-summary">
        {question.matrix_rows.map((row) => (
          <div key={row.row}>
            <Typography.Text strong>{row.row}</Typography.Text>
            {renderChoiceCounts(row.choice_counts)}
          </div>
        ))}
      </Space>
    );
  }

  if (question.type === "TEXT") {
    if (!question.text_answers.length) return <Typography.Text type="secondary">No answers</Typography.Text>;
    return (
      <Space direction="vertical" size={4} className="text-samples">
        {question.text_answers.slice(0, 3).map((answer, index) => (
          <Typography.Paragraph key={`${answer}-${index}`} ellipsis={{ rows: 2 }}>
            {answer}
          </Typography.Paragraph>
        ))}
        {question.text_answers.length > 3 && <Tag>{question.text_answers.length - 3} more</Tag>}
      </Space>
    );
  }

  return renderChoiceCounts(question.choice_counts);
}

export function AnalyticsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const { data: overview } = useQuery({
    queryKey: ["analytics-overview"],
    queryFn: () => apiRequest<AnalyticsOverview>("/analytics/overview")
  });
  const { data: surveys = [], isLoading: surveysLoading } = useQuery({
    queryKey: ["surveys"],
    queryFn: () => apiRequest<Survey[]>("/surveys")
  });

  const selectedSurveyId = searchParams.get("surveyId") ?? surveys[0]?.id;
  const {
    data: surveyAnalytics,
    isError: surveyAnalyticsError,
    isLoading: surveyAnalyticsLoading
  } = useQuery({
    queryKey: ["survey-analytics", selectedSurveyId],
    queryFn: () => apiRequest<SurveyAnalytics>(`/analytics/surveys/${selectedSurveyId as string}`),
    enabled: Boolean(selectedSurveyId)
  });

  const chartData = [
    { name: "Completion", value: overview?.completion_rate ?? 0 },
    { name: "Response", value: overview?.response_rate ?? 0 },
    { name: "eNPS", value: overview?.enps ?? 0 }
  ];
  const latestResponses = overview?.latest_responses ?? [];
  const notificationData = Object.entries(overview?.notification_efficiency ?? {}).map(([channel, stats]) => ({
    channel,
    ...stats
  }));
  const surveyRateData = [
    { name: "Completion", value: surveyAnalytics?.completion_rate ?? 0 },
    { name: "Response", value: surveyAnalytics?.response_rate ?? 0 },
    { name: "eNPS", value: surveyAnalytics?.enps ?? 0 }
  ];

  const responseRows = useMemo<ResponseTableRow[]>(
    () =>
      (surveyAnalytics?.responses ?? []).map((response) => ({
        ...response,
        answerMap: Object.fromEntries(
          response.answers.map((answer) => [answer.question_id, answer.display_value])
        )
      })),
    [surveyAnalytics]
  );

  const summaryColumns: ColumnsType<QuestionAnalyticsSummary> = [
    { title: "#", dataIndex: "position", width: 72, render: (position: number) => position + 1 },
    { title: "Question", dataIndex: "title", width: 280 },
    { title: "Type", dataIndex: "type", width: 160, render: (type: QuestionType) => <Tag>{type}</Tag> },
    {
      title: "Answers",
      dataIndex: "answer_count",
      width: 120,
      render: (count: number, record) => `${count}/${count + record.skipped_count}`
    },
    { title: "Summary", render: (_value, record) => renderQuestionSummary(record) }
  ];

  const responseColumns = useMemo<ColumnsType<ResponseTableRow>>(
    () => [
      {
        title: "Respondent",
        fixed: "left",
        width: 240,
        render: (_value, record) => (
          <Space direction="vertical" size={0}>
            <Typography.Text strong>{record.respondent.label}</Typography.Text>
            {record.respondent.anonymous ? (
              <Tag color="green">Anonymous</Tag>
            ) : (
              <Typography.Text type="secondary">{record.respondent.phone ?? "No phone"}</Typography.Text>
            )}
          </Space>
        )
      },
      {
        title: "Department",
        width: 160,
        render: (_value, record) => record.respondent.department ?? "Unknown"
      },
      {
        title: "Position",
        width: 160,
        render: (_value, record) => record.respondent.position ?? "Unknown"
      },
      {
        title: "Submitted",
        dataIndex: "submitted_at",
        width: 190,
        render: (value: string | null) => formatDate(value)
      },
      ...(surveyAnalytics?.question_summaries ?? []).map((question) => ({
        title: question.title,
        width: 240,
        render: (_value: unknown, record: ResponseTableRow) => (
          <Typography.Text className="analytics-answer-text">
            {record.answerMap[question.question_id] || "No answer"}
          </Typography.Text>
        )
      }))
    ],
    [surveyAnalytics?.question_summaries]
  );

  return (
    <>
      <div className="toolbar">
        <h2>Analytics</h2>
        <Select
          className="survey-analytics-select"
          loading={surveysLoading}
          options={surveys.map((survey) => ({ label: survey.title, value: survey.id }))}
          placeholder="Select survey"
          value={selectedSurveyId}
          onChange={(surveyId) => setSearchParams({ surveyId })}
        />
      </div>

      <div className="grid analytics-stat-grid">
        <Card><Statistic title="Active surveys" value={overview?.active_surveys ?? 0} /></Card>
        <Card><Statistic title="Completion rate" value={overview?.completion_rate ?? 0} suffix="%" /></Card>
        <Card><Statistic title="Response rate" value={overview?.response_rate ?? 0} suffix="%" /></Card>
        <Card><Statistic title="eNPS" value={overview?.enps ?? "N/A"} /></Card>
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

      {selectedSurveyId ? (
        surveyAnalytics ? (
          <>
            <Card
              title={
                <Space wrap>
                  <span>{surveyAnalytics.title}</span>
                  {surveyAnalytics.is_anonymous && <Tag color="green">Anonymous</Tag>}
                </Space>
              }
              style={{ marginTop: 16 }}
            >
              <div className="grid survey-analytics-stat-grid">
                <Statistic title="Assigned" value={surveyAnalytics.assigned_count} />
                <Statistic title="Submitted" value={surveyAnalytics.submitted_count} />
                <Statistic title="Started responses" value={surveyAnalytics.response_count} />
                <Statistic title="Completion rate" value={surveyAnalytics.completion_rate} suffix="%" />
                <Statistic title="Response rate" value={surveyAnalytics.response_rate} suffix="%" />
                <Statistic title="eNPS" value={surveyAnalytics.enps ?? "N/A"} />
              </div>
            </Card>

            <div className="analytics-layout survey-analytics-charts">
              <Card title="Survey rates">
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart data={surveyRateData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="value" fill="#1677ff" />
                  </BarChart>
                </ResponsiveContainer>
              </Card>

              <Card title="Departments">
                {surveyAnalytics.department_analytics.length ? (
                  <ResponsiveContainer width="100%" height={260}>
                    <BarChart data={surveyAnalytics.department_analytics}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="label" />
                      <YAxis />
                      <Tooltip />
                      <Bar dataKey="value" fill="#52c41a" />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No submitted responses" />
                )}
              </Card>
            </div>

            <Card style={{ marginTop: 16 }}>
              <Tabs
                items={[
                  {
                    key: "summary",
                    label: "Summary",
                    children: (
                      <Table
                        rowKey="question_id"
                        dataSource={surveyAnalytics.question_summaries}
                        columns={summaryColumns}
                        pagination={false}
                      />
                    )
                  },
                  {
                    key: "responses",
                    label: "Responses",
                    children: (
                      <Table
                        rowKey="response_id"
                        dataSource={responseRows}
                        columns={responseColumns}
                        pagination={{ pageSize: 8 }}
                        scroll={{ x: 760 + surveyAnalytics.question_summaries.length * 240 }}
                      />
                    )
                  },
                  {
                    key: "timeline",
                    label: "Timeline",
                    children: surveyAnalytics.timeline.length ? (
                      <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={surveyAnalytics.timeline}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="date" />
                          <YAxis />
                          <Tooltip />
                          <Bar dataKey="responses" fill="#faad14" />
                        </BarChart>
                      </ResponsiveContainer>
                    ) : (
                      <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No submitted responses" />
                    )
                  }
                ]}
              />
            </Card>
          </>
        ) : (
          <Card loading={surveyAnalyticsLoading} style={{ marginTop: 16 }}>
            {!surveyAnalyticsLoading && (
              <Empty
                image={Empty.PRESENTED_IMAGE_SIMPLE}
                description={surveyAnalyticsError ? "Survey analytics unavailable" : "No analytics"}
              />
            )}
          </Card>
        )
      ) : (
        <Card style={{ marginTop: 16 }}>
          <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No surveys" />
        </Card>
      )}
    </>
  );
}
