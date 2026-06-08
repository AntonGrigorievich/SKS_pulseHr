import { useMutation, useQuery } from "@tanstack/react-query";
import { Alert, Button, Card, Space, Typography, message } from "antd";
import { useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { apiRequest } from "../../api/client";
import { SurveyDetail } from "../../api/types";
import { QuestionRenderer } from "../../components/QuestionRenderer";
import { visibleQuestions as evaluateVisibleQuestions } from "../../features/surveyLogic/evaluateRules";

export function SurveyPassPage() {
  const { surveyId } = useParams();
  const [responseId, setResponseId] = useState<string | null>(null);
  const [answers, setAnswers] = useState<Record<string, Record<string, unknown>>>({});

  const { data: survey } = useQuery({
    queryKey: ["employee-survey", surveyId],
    queryFn: () => apiRequest<SurveyDetail>(`/employee/surveys/${surveyId}`),
    enabled: Boolean(surveyId)
  });

  const start = useMutation({
    mutationFn: () => apiRequest<{ response_id: string; warning: string }>(`/employee/surveys/${surveyId}/start`, { method: "POST" }),
    onSuccess: (data) => {
      setResponseId(data.response_id);
      message.info(data.warning);
    }
  });

  const saveAnswer = useMutation({
    mutationFn: ({ questionId, value }: { questionId: string; value: Record<string, unknown> }) =>
      apiRequest(`/responses/${responseId}/answers`, {
        method: "POST",
        body: JSON.stringify({ question_id: questionId, value })
      })
  });

  const submit = useMutation({
    mutationFn: () => apiRequest(`/responses/${responseId}/submit`, { method: "POST" }),
    onSuccess: () => message.success("Submitted")
  });

  const visibleQuestions = useMemo(
    () => (survey ? evaluateVisibleQuestions(survey.questions, survey.rules, answers) : []),
    [answers, survey]
  );

  if (!survey) return null;

  return (
    <Card>
      <Typography.Title level={2}>{survey.title}</Typography.Title>
      <Alert
        type={survey.is_anonymous ? "success" : "warning"}
        message={
          survey.is_anonymous
            ? "Этот опрос анонимный. HR не сможет определить автора ответа."
            : "Ваши ответы будут доступны HR."
        }
        style={{ marginBottom: 16 }}
      />
      {!responseId && <Button type="primary" onClick={() => start.mutate()}>Start</Button>}
      {responseId && (
        <Space direction="vertical" style={{ width: "100%" }}>
          {visibleQuestions.map((question) => (
            <Card key={question.id} className="question-row">
              <Typography.Title level={5}>{question.title}</Typography.Title>
              <QuestionRenderer
                question={question}
                value={answers[question.id]}
                onChange={(value) => {
                  setAnswers((state) => ({ ...state, [question.id]: value }));
                  saveAnswer.mutate({ questionId: question.id, value });
                }}
              />
            </Card>
          ))}
          <Button type="primary" onClick={() => submit.mutate()} loading={submit.isPending}>Submit</Button>
        </Space>
      )}
    </Card>
  );
}
