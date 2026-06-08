import { ClockCircleOutlined } from "@ant-design/icons";
import { useQuery } from "@tanstack/react-query";
import { Button, Card, Progress, Space, Tag, Typography } from "antd";
import { Link } from "react-router-dom";
import { apiRequest } from "../../api/client";
import { EmployeeSurveyCard } from "../../api/types";

export function SurveyListPage() {
  const { data = [] } = useQuery({
    queryKey: ["employee-surveys"],
    queryFn: () => apiRequest<EmployeeSurveyCard[]>("/employee/surveys")
  });

  return (
    <div className="grid">
      {data.map((survey) => (
        <Card key={survey.id}>
          <Typography.Title level={4}>{survey.title}</Typography.Title>
          <Typography.Paragraph>{survey.description}</Typography.Paragraph>
          <Space wrap>
            <Tag>{survey.status}</Tag>
            <Tag icon={<ClockCircleOutlined />}>{survey.estimated_minutes} min</Tag>
          </Space>
          <Progress percent={survey.completion_percent} />
          <Button type="primary">
            <Link to={`/employee/surveys/${survey.id}`}>Open</Link>
          </Button>
        </Card>
      ))}
    </div>
  );
}

