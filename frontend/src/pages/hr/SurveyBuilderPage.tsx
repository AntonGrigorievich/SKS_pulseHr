import { DndContext, DragEndEvent } from "@dnd-kit/core";
import { SortableContext, arrayMove, useSortable, verticalListSortingStrategy } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Button, Card, Form, Input, Modal, Select, Space, Switch, Tabs } from "antd";
import { useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { apiRequest } from "../../api/client";
import { Question, QuestionType, SurveyDetail } from "../../api/types";

function SortableQuestion({ question }: { question: Question }) {
  const { attributes, listeners, setNodeRef, transform, transition } = useSortable({ id: question.id });
  return (
    <Card ref={setNodeRef} style={{ transform: CSS.Transform.toString(transform), transition, marginBottom: 8 }} {...attributes} {...listeners}>
      <b>{question.position + 1}. {question.title}</b>
      <div>{question.type}</div>
    </Card>
  );
}

export function SurveyBuilderPage() {
  const { surveyId } = useParams();
  const [open, setOpen] = useState(false);
  const queryClient = useQueryClient();
  const { data } = useQuery({
    queryKey: ["survey-detail", surveyId],
    queryFn: () => apiRequest<SurveyDetail>(`/surveys/${surveyId}`),
    enabled: Boolean(surveyId)
  });
  const questions = useMemo(() => [...(data?.questions ?? [])].sort((a, b) => a.position - b.position), [data]);

  const createQuestion = useMutation({
    mutationFn: (payload: { title: string; type: QuestionType; is_required: boolean }) =>
      apiRequest(`/surveys/${surveyId}/questions`, {
        method: "POST",
        body: JSON.stringify({ ...payload, position: questions.length, settings: {}, options: [] })
      }),
    onSuccess: () => {
      setOpen(false);
      queryClient.invalidateQueries({ queryKey: ["survey-detail", surveyId] });
    }
  });
  const reorder = useMutation({
    mutationFn: (items: { id: string; position: number }[]) =>
      apiRequest(`/surveys/${surveyId}/questions/reorder`, { method: "POST", body: JSON.stringify({ items }) }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["survey-detail", surveyId] })
  });
  const createRule = useMutation({
    mutationFn: (payload: Record<string, unknown>) =>
      apiRequest(`/surveys/${surveyId}/rules`, { method: "POST", body: JSON.stringify(payload) }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["survey-detail", surveyId] })
  });

  function onDragEnd(event: DragEndEvent) {
    if (!event.over || event.active.id === event.over.id) return;
    const oldIndex = questions.findIndex((item) => item.id === event.active.id);
    const newIndex = questions.findIndex((item) => item.id === event.over?.id);
    const ordered = arrayMove(questions, oldIndex, newIndex).map((question, position) => ({ id: question.id, position }));
    reorder.mutate(ordered);
  }

  return (
    <>
      <div className="toolbar">
        <h2>{data?.title}</h2>
        <Button type="primary" onClick={() => setOpen(true)}>Add Question</Button>
      </div>
      <Tabs
        items={[
          {
            key: "questions",
            label: "Questions",
            children: (
              <DndContext onDragEnd={onDragEnd}>
                <SortableContext items={questions.map((item) => item.id)} strategy={verticalListSortingStrategy}>
                  {questions.map((question) => <SortableQuestion key={question.id} question={question} />)}
                </SortableContext>
              </DndContext>
            )
          },
          {
            key: "rules",
            label: "Rules",
            children: (
              <Space direction="vertical" style={{ width: "100%" }}>
                {(data?.rules ?? []).map((rule) => <Card key={rule.id}>{rule.name}</Card>)}
                <Form
                  layout="vertical"
                  onFinish={(values) =>
                    createRule.mutate({
                      ...values,
                      priority: Number(values.priority ?? 100),
                      condition: { op: "AND", conditions: [{ field: values.field, operator: values.operator, value: values.value }] }
                    })
                  }
                >
                  <Form.Item name="name" label="Name" rules={[{ required: true }]}><Input /></Form.Item>
                  <Form.Item name="target_question_id" label="Target" rules={[{ required: true }]}>
                    <Select options={questions.map((q) => ({ label: q.title, value: q.id }))} />
                  </Form.Item>
                  <Form.Item name="action" label="Action" initialValue="SHOW_QUESTION"><Select options={[{ value: "SHOW_QUESTION" }, { value: "HIDE_QUESTION" }]} /></Form.Item>
                  <Form.Item name="field" label="Field"><Input placeholder="user.position" /></Form.Item>
                  <Form.Item name="operator" label="Operator" initialValue="equals"><Select options={[{ value: "equals" }, { value: "lte" }, { value: "gte" }, { value: "in" }]} /></Form.Item>
                  <Form.Item name="value" label="Value"><Input /></Form.Item>
                  <Button htmlType="submit">Add rule</Button>
                </Form>
              </Space>
            )
          }
        ]}
      />
      <Modal title="Add question" open={open} onCancel={() => setOpen(false)} footer={null}>
        <Form layout="vertical" onFinish={(values) => createQuestion.mutate(values)}>
          <Form.Item name="title" label="Title" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="type" label="Type" initialValue="TEXT">
            <Select options={["SINGLE_CHOICE", "MULTIPLE_CHOICE", "RATING", "TEXT", "MATRIX"].map((value) => ({ value }))} />
          </Form.Item>
          <Form.Item name="is_required" label="Required" valuePropName="checked" initialValue><Switch /></Form.Item>
          <Button type="primary" htmlType="submit">Add</Button>
        </Form>
      </Modal>
    </>
  );
}

