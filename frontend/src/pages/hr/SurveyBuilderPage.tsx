import {
  DeleteOutlined,
  EditOutlined,
  LinkOutlined,
  PlusOutlined,
  SaveOutlined
} from "@ant-design/icons";
import { DndContext, DragEndEvent } from "@dnd-kit/core";
import { SortableContext, arrayMove, useSortable, verticalListSortingStrategy } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Button,
  Card,
  Form,
  Input,
  InputNumber,
  Modal,
  Popconfirm,
  Select,
  Space,
  Switch,
  Tabs,
  Tag,
  Typography,
  message
} from "antd";
import { PointerEvent, useMemo, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import { apiRequest } from "../../api/client";
import {
  BlueprintPosition,
  BranchOperator,
  Question,
  QuestionOption,
  QuestionType,
  SurveyDetail,
  SurveyRule
} from "../../api/types";

const QUESTION_TYPES: QuestionType[] = ["SINGLE_CHOICE", "MULTIPLE_CHOICE", "RATING", "TEXT", "MATRIX"];
const RULE_ACTIONS = ["SHOW_QUESTION", "HIDE_QUESTION"] as const;
const OPERATORS: BranchOperator[] = ["equals", "lte", "gte", "in"];
const NODE_WIDTH = 280;
const NODE_HEIGHT = 180;

type RuleAction = (typeof RULE_ACTIONS)[number];
type QuestionFormValues = {
  title: string;
  description?: string | null;
  type: QuestionType;
  is_required: boolean;
  options?: QuestionOption[];
  max?: number;
  rowsText?: string;
  columnsText?: string;
};
type ConnectionDraft = {
  sourceQuestionId: string;
  sourceKey: string;
  sourceValue?: string | number;
  targetQuestionId: string;
};
type RuleFormValues = {
  sourceQuestionId: string;
  sourceKey: string;
  target_question_id: string;
  operator: BranchOperator;
  value: string | number | string[];
  action: RuleAction;
  priority: number;
  name?: string;
};
type ParsedRule = {
  field: string;
  sourceQuestionId: string;
  sourceKey: string;
  operator: BranchOperator;
  value: unknown;
};
type DragState = {
  questionId: string;
  startX: number;
  startY: number;
  origin: BlueprintPosition;
};

function SortableQuestion({ question, onEdit, onDelete }: { question: Question; onEdit: (question: Question) => void; onDelete: (question: Question) => void }) {
  const { attributes, listeners, setNodeRef, transform, transition } = useSortable({ id: question.id });
  return (
    <Card ref={setNodeRef} style={{ transform: CSS.Transform.toString(transform), transition, marginBottom: 8 }}>
      <div className="builder-list-row">
        <div {...attributes} {...listeners} className="builder-list-drag">
          <b>{question.position + 1}. {question.title}</b>
          <div>{question.type}</div>
        </div>
        <Space>
          <Button icon={<EditOutlined />} onClick={() => onEdit(question)} />
          <Popconfirm title="Delete question?" onConfirm={() => onDelete(question)}>
            <Button danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      </div>
    </Card>
  );
}

function isChoiceQuestion(question: Question | QuestionType) {
  const type = typeof question === "string" ? question : question.type;
  return type === "SINGLE_CHOICE" || type === "MULTIPLE_CHOICE";
}

function getBlueprintPosition(question: Question, index: number): BlueprintPosition {
  const blueprint = question.settings?.blueprint as { position?: Partial<BlueprintPosition> } | undefined;
  const saved = blueprint?.position;
  if (typeof saved?.x === "number" && typeof saved?.y === "number") return { x: saved.x, y: saved.y };
  return { x: 40 + (index % 3) * 360, y: 40 + Math.floor(index / 3) * 260 };
}

function buildSettings(values: QuestionFormValues, existing?: Question): Record<string, unknown> {
  const settings = { ...(existing?.settings ?? {}) };
  if (values.type === "RATING") {
    settings.max = values.max ?? Number(settings.max ?? 10);
  }
  if (values.type === "MATRIX") {
    settings.rows = splitLines(values.rowsText) || ((settings.rows as string[] | undefined) ?? []);
    settings.columns = splitLines(values.columnsText) || ((settings.columns as string[] | undefined) ?? ["1", "2", "3", "4", "5"]);
  }
  return settings;
}

function splitLines(value?: string) {
  const items = (value ?? "").split(/\r?\n|,/).map((item) => item.trim()).filter(Boolean);
  return items.length > 0 ? items : undefined;
}

function normalizeOptions(values: QuestionFormValues): QuestionOption[] {
  if (!isChoiceQuestion(values.type)) return [];
  return (values.options ?? [])
    .filter((option) => option.label?.trim() || option.value?.trim())
    .map((option, position) => ({
      label: option.label?.trim() || option.value.trim(),
      value: option.value?.trim() || option.label.trim(),
      position
    }));
}

function getOutputKeys(question: Question) {
  if (question.type === "SINGLE_CHOICE") return question.options.map((option) => ({ key: "option", label: option.label, value: option.value }));
  if (question.type === "MULTIPLE_CHOICE") return question.options.map((option) => ({ key: "options", label: option.label, value: option.value }));
  if (question.type === "RATING") return [{ key: "score", label: "Score", value: "" }];
  if (question.type === "MATRIX") return ((question.settings.rows as string[] | undefined) ?? []).map((row) => ({ key: `rows.${row}`, label: row, value: "" }));
  return [{ key: "text", label: "Text", value: "" }];
}

function getSourceFieldOptions(question: Question) {
  const labels = new Map<string, string>();
  for (const output of getOutputKeys(question)) {
    if (!labels.has(output.key)) labels.set(output.key, output.key);
  }
  return [...labels.entries()].map(([value, label]) => ({ value, label }));
}

function buildField(questionId: string, key: string) {
  return `answers.${questionId}.${key}`;
}

function normalizeRuleValue(operator: BranchOperator, value: RuleFormValues["value"]) {
  if (operator === "in") {
    if (Array.isArray(value)) return value;
    return String(value)
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean);
  }
  return value;
}

function valuesMatch(left: unknown, right: unknown) {
  return JSON.stringify(left) === JSON.stringify(right);
}

function withBlueprintPosition(settings: Record<string, unknown>, position: BlueprintPosition) {
  return {
    ...settings,
    blueprint: {
      ...((settings.blueprint as Record<string, unknown> | undefined) ?? {}),
      position
    }
  };
}

function parseRule(rule: SurveyRule): ParsedRule | null {
  const conditions = (rule.condition.conditions as Record<string, unknown>[] | undefined) ?? [];
  const condition = conditions.find((item) => typeof item.field === "string" && String(item.field).startsWith("answers."));
  if (!condition || typeof condition.field !== "string" || typeof condition.operator !== "string") return null;
  const [, sourceQuestionId, ...keyParts] = condition.field.split(".");
  if (!sourceQuestionId || keyParts.length === 0) return null;
  if (!OPERATORS.includes(condition.operator as BranchOperator)) return null;
  return {
    field: condition.field,
    sourceQuestionId,
    sourceKey: keyParts.join("."),
    operator: condition.operator as BranchOperator,
    value: condition.value
  };
}

function formatRuleName(questions: Question[], values: RuleFormValues) {
  const source = questions.find((question) => question.id === values.sourceQuestionId);
  const target = questions.find((question) => question.id === values.target_question_id);
  const action = values.action === "SHOW_QUESTION" ? "Show" : "Hide";
  return `${action} "${target?.title ?? "target"}" when "${source?.title ?? "source"}" ${values.operator} "${String(values.value)}"`;
}

function getInitialQuestionValues(question?: Question): Partial<QuestionFormValues> {
  return {
    title: question?.title ?? "",
    description: question?.description ?? "",
    type: question?.type ?? "TEXT",
    is_required: question?.is_required ?? true,
    options: question?.options?.length ? question.options : [{ label: "Yes", value: "yes", position: 0 }],
    max: Number(question?.settings.max ?? 10),
    rowsText: ((question?.settings.rows as string[] | undefined) ?? []).join("\n"),
    columnsText: ((question?.settings.columns as string[] | undefined) ?? ["1", "2", "3", "4", "5"]).join("\n")
  };
}

export function SurveyBuilderPage() {
  const { surveyId } = useParams();
  const [questionModalOpen, setQuestionModalOpen] = useState(false);
  const [editingQuestion, setEditingQuestion] = useState<Question | null>(null);
  const [ruleModalOpen, setRuleModalOpen] = useState(false);
  const [editingRule, setEditingRule] = useState<SurveyRule | null>(null);
  const [connectionDraft, setConnectionDraft] = useState<ConnectionDraft | null>(null);
  const [positions, setPositions] = useState<Record<string, BlueprintPosition>>({});
  const [dragState, setDragState] = useState<DragState | null>(null);
  const [questionForm] = Form.useForm<QuestionFormValues>();
  const [ruleForm] = Form.useForm<RuleFormValues>();
  const canvasRef = useRef<HTMLDivElement | null>(null);
  const queryClient = useQueryClient();

  const { data } = useQuery({
    queryKey: ["survey-detail", surveyId],
    queryFn: () => apiRequest<SurveyDetail>(`/surveys/${surveyId}`),
    enabled: Boolean(surveyId)
  });
  const questions = useMemo(() => [...(data?.questions ?? [])].sort((a, b) => a.position - b.position), [data]);
  const questionIds = useMemo(() => new Set(questions.map((question) => question.id)), [questions]);
  const parsedRules = useMemo(
    () => (data?.rules ?? []).map((rule) => ({ rule, parsed: parseRule(rule) })).filter((item) => item.parsed),
    [data?.rules]
  );
  const nodePositions = useMemo(
    () => Object.fromEntries(questions.map((question, index) => [question.id, positions[question.id] ?? getBlueprintPosition(question, index)])),
    [positions, questions]
  );

  const invalidateSurvey = () => queryClient.invalidateQueries({ queryKey: ["survey-detail", surveyId] });
  const createQuestion = useMutation({
    mutationFn: (payload: Record<string, unknown>) =>
      apiRequest<Question>(`/surveys/${surveyId}/questions`, { method: "POST", body: JSON.stringify(payload) }),
    onSuccess: (question) => {
      setQuestionModalOpen(false);
      setEditingQuestion(null);
      setPositions((state) => ({ ...state, [question.id]: getBlueprintPosition(question, questions.length) }));
      invalidateSurvey();
    }
  });
  const updateQuestion = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: Record<string, unknown> }) =>
      apiRequest<Question>(`/questions/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
    onSuccess: () => {
      setQuestionModalOpen(false);
      setEditingQuestion(null);
      invalidateSurvey();
    }
  });
  const deleteQuestion = useMutation({
    mutationFn: (id: string) => apiRequest(`/questions/${id}`, { method: "DELETE" }),
    onSuccess: () => invalidateSurvey()
  });
  const reorder = useMutation({
    mutationFn: (items: { id: string; position: number }[]) =>
      apiRequest(`/surveys/${surveyId}/questions/reorder`, { method: "POST", body: JSON.stringify({ items }) }),
    onSuccess: () => invalidateSurvey()
  });
  const createRule = useMutation({
    mutationFn: (payload: Record<string, unknown>) =>
      apiRequest<SurveyRule>(`/surveys/${surveyId}/rules`, { method: "POST", body: JSON.stringify(payload) }),
    onSuccess: () => {
      setRuleModalOpen(false);
      setConnectionDraft(null);
      invalidateSurvey();
    }
  });
  const updateRule = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: Record<string, unknown> }) =>
      apiRequest<SurveyRule>(`/rules/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
    onSuccess: () => {
      setRuleModalOpen(false);
      setEditingRule(null);
      invalidateSurvey();
    }
  });
  const deleteRule = useMutation({
    mutationFn: (id: string) => apiRequest(`/rules/${id}`, { method: "DELETE" }),
    onSuccess: () => {
      setRuleModalOpen(false);
      setEditingRule(null);
      invalidateSurvey();
    }
  });

  function openQuestionModal(question?: Question) {
    setEditingQuestion(question ?? null);
    questionForm.setFieldsValue(getInitialQuestionValues(question));
    setQuestionModalOpen(true);
  }

  function submitQuestion(values: QuestionFormValues) {
    const initialPosition = getBlueprintPosition({ settings: {}, position: questions.length } as Question, questions.length);
    const payload = {
      title: values.title,
      description: values.description ?? null,
      type: values.type,
      is_required: values.is_required,
      position: editingQuestion?.position ?? questions.length,
      settings: editingQuestion
        ? buildSettings(values, editingQuestion)
        : withBlueprintPosition(buildSettings(values), initialPosition),
      options: normalizeOptions(values)
    };
    if (editingQuestion) {
      updateQuestion.mutate({ id: editingQuestion.id, payload });
      return;
    }
    createQuestion.mutate(payload);
  }

  function onDragEnd(event: DragEndEvent) {
    if (!event.over || event.active.id === event.over.id) return;
    const oldIndex = questions.findIndex((item) => item.id === event.active.id);
    const newIndex = questions.findIndex((item) => item.id === event.over?.id);
    const ordered = arrayMove(questions, oldIndex, newIndex).map((question, position) => ({ id: question.id, position }));
    reorder.mutate(ordered);
  }

  function beginNodeDrag(event: PointerEvent<HTMLDivElement>, question: Question) {
    if ((event.target as HTMLElement).closest("button")) return;
    event.currentTarget.setPointerCapture(event.pointerId);
    setDragState({
      questionId: question.id,
      startX: event.clientX,
      startY: event.clientY,
      origin: nodePositions[question.id]
    });
  }

  function moveNode(event: PointerEvent<HTMLDivElement>) {
    if (!dragState) return;
    const next = {
      x: Math.max(0, dragState.origin.x + event.clientX - dragState.startX),
      y: Math.max(0, dragState.origin.y + event.clientY - dragState.startY)
    };
    setPositions((state) => ({ ...state, [dragState.questionId]: next }));
  }

  function endNodeDrag(event?: PointerEvent<HTMLDivElement>) {
    if (!dragState) return;
    const question = questions.find((item) => item.id === dragState.questionId);
    const position = event
      ? {
          x: Math.max(0, dragState.origin.x + event.clientX - dragState.startX),
          y: Math.max(0, dragState.origin.y + event.clientY - dragState.startY)
        }
      : positions[dragState.questionId] ?? nodePositions[dragState.questionId];
    setDragState(null);
    if (!question || !position) return;
    setPositions((state) => ({ ...state, [question.id]: position }));
    const settings = withBlueprintPosition(question.settings, position);
    updateQuestion.mutate({ id: question.id, payload: { settings } });
  }

  function openRuleModal(draft: ConnectionDraft, rule?: SurveyRule) {
    if (draft.sourceQuestionId === draft.targetQuestionId) {
      message.warning("Self-connections are not allowed");
      return;
    }
    if (!questionIds.has(draft.sourceQuestionId) || !questionIds.has(draft.targetQuestionId)) {
      message.error("Connection questions must belong to this survey");
      return;
    }
    const source = questions.find((question) => question.id === draft.sourceQuestionId);
    const output = source
      ? getOutputKeys(source).find((item) => item.key === draft.sourceKey && item.value === draft.sourceValue)
      : undefined;
    setEditingRule(rule ?? null);
    setConnectionDraft(draft);
    ruleForm.setFieldsValue({
      sourceQuestionId: draft.sourceQuestionId,
      sourceKey: draft.sourceKey,
      target_question_id: draft.targetQuestionId,
      operator: (rule && parseRule(rule)?.operator) ?? "equals",
      value: (rule && (parseRule(rule)?.value as string | number | string[])) ?? output?.value ?? draft.sourceValue ?? "",
      action: rule?.action ?? "SHOW_QUESTION",
      priority: rule?.priority ?? 100,
      name: rule?.name
    });
    setRuleModalOpen(true);
  }

  function submitRule(values: RuleFormValues) {
    if (values.sourceQuestionId === values.target_question_id) {
      message.warning("Self-connections are not allowed");
      return;
    }
    if (!questionIds.has(values.sourceQuestionId) || !questionIds.has(values.target_question_id)) {
      message.error("Rule questions must belong to this survey");
      return;
    }
    const field = buildField(values.sourceQuestionId, values.sourceKey);
    const ruleValue = normalizeRuleValue(values.operator, values.value);
    const duplicate = (data?.rules ?? []).find((rule) => {
      if (editingRule?.id === rule.id) return false;
      const parsed = parseRule(rule);
      return (
        parsed?.field === field &&
        parsed.operator === values.operator &&
        valuesMatch(parsed.value, ruleValue) &&
        rule.target_question_id === values.target_question_id &&
        rule.action === values.action
      );
    });
    if (duplicate) {
      message.warning("A matching branch rule already exists");
      return;
    }
    const payload = {
      target_question_id: values.target_question_id,
      name: values.name?.trim() || formatRuleName(questions, values),
      priority: Number(values.priority ?? 100),
      action: values.action,
      condition: { op: "AND", conditions: [{ field, operator: values.operator, value: ruleValue }] }
    };
    if (editingRule) updateRule.mutate({ id: editingRule.id, payload });
    else createRule.mutate(payload);
  }

  function editExistingRule(rule: SurveyRule) {
    const parsed = parseRule(rule);
    if (!parsed) return;
    openRuleModal(
      { sourceQuestionId: parsed.sourceQuestionId, sourceKey: parsed.sourceKey, targetQuestionId: rule.target_question_id },
      rule
    );
  }

  const canvasWidth = Math.max(1100, ...Object.values(nodePositions).map((position) => position.x + NODE_WIDTH + 80));
  const canvasHeight = Math.max(680, ...Object.values(nodePositions).map((position) => position.y + NODE_HEIGHT + 100));

  return (
    <>
      <div className="toolbar">
        <div>
          <Typography.Title level={2} style={{ margin: 0 }}>{data?.title}</Typography.Title>
          <Typography.Text type="secondary">Survey builder</Typography.Text>
        </div>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => openQuestionModal()}>Add question</Button>
      </div>
      <Tabs
        items={[
          {
            key: "blueprint",
            label: "Blueprint",
            children: (
              <div className="blueprint-shell">
                <div className="blueprint-topbar">
                  <Space>
                    <Button type="primary" icon={<PlusOutlined />} onClick={() => openQuestionModal()}>Add question</Button>
                    {connectionDraft && (
                      <Tag color="processing">
                        Linking from {questions.find((question) => question.id === connectionDraft.sourceQuestionId)?.title}
                      </Tag>
                    )}
                  </Space>
                  <Typography.Text type="secondary">{questions.length} questions / {(data?.rules ?? []).length} rules</Typography.Text>
                </div>
                <div className="blueprint-workspace">
                  <div className="blueprint-canvas" ref={canvasRef} style={{ width: canvasWidth, height: canvasHeight }}>
                    <svg className="blueprint-edges" width={canvasWidth} height={canvasHeight}>
                      <defs>
                        <marker id="edge-arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto">
                          <path d="M0,0 L0,6 L9,3 z" fill="#3b6ea8" />
                        </marker>
                      </defs>
                      {parsedRules.map(({ rule, parsed }) => {
                        if (!parsed) return null;
                        const source = nodePositions[parsed.sourceQuestionId];
                        const target = nodePositions[rule.target_question_id];
                        if (!source || !target) return null;
                        const start = { x: source.x + NODE_WIDTH, y: source.y + 88 };
                        const end = { x: target.x, y: target.y + 88 };
                        const midX = start.x + (end.x - start.x) / 2;
                        return (
                          <g key={rule.id} className="blueprint-edge" onClick={() => editExistingRule(rule)}>
                            <path
                              d={`M ${start.x} ${start.y} C ${midX} ${start.y}, ${midX} ${end.y}, ${end.x} ${end.y}`}
                              markerEnd="url(#edge-arrow)"
                            />
                            <text x={midX} y={(start.y + end.y) / 2 - 8}>{rule.action === "SHOW_QUESTION" ? "show" : "hide"}</text>
                          </g>
                        );
                      })}
                    </svg>
                    {questions.map((question) => {
                      const position = nodePositions[question.id];
                      const outputs = getOutputKeys(question);
                      return (
                        <div
                          key={question.id}
                          className="blueprint-node"
                          style={{ left: position.x, top: position.y, width: NODE_WIDTH }}
                          onPointerDown={(event) => beginNodeDrag(event, question)}
                          onPointerMove={moveNode}
                          onPointerUp={(event) => endNodeDrag(event)}
                          onPointerCancel={(event) => endNodeDrag(event)}
                        >
                          <div className="blueprint-node-header">
                            <div>
                              <Typography.Text strong ellipsis>{question.title}</Typography.Text>
                              <div>
                                <Tag>{question.type}</Tag>
                                {question.is_required && <Tag color="red">required</Tag>}
                              </div>
                            </div>
                            <Space size={4}>
                              <Button size="small" icon={<EditOutlined />} onClick={() => openQuestionModal(question)} />
                              <Popconfirm title="Delete question?" onConfirm={() => deleteQuestion.mutate(question.id)}>
                                <Button size="small" danger icon={<DeleteOutlined />} />
                              </Popconfirm>
                            </Space>
                          </div>
                          <button
                            type="button"
                            className="blueprint-target"
                            onClick={() => {
                              if (connectionDraft) openRuleModal({ ...connectionDraft, targetQuestionId: question.id });
                            }}
                          >
                            Input
                          </button>
                          <div className="blueprint-outputs">
                            {outputs.map((output) => (
                              <button
                                type="button"
                                key={`${output.key}:${output.value}`}
                                className="blueprint-output"
                                onClick={() =>
                                  setConnectionDraft({
                                    sourceQuestionId: question.id,
                                    sourceKey: output.key,
                                    sourceValue: output.value,
                                    targetQuestionId: ""
                                  })
                                }
                              >
                                <span>{output.label}</span>
                                <LinkOutlined />
                              </button>
                            ))}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
                <aside className="blueprint-inspector">
                  <Typography.Title level={5}>Rules</Typography.Title>
                  <Space direction="vertical" style={{ width: "100%" }}>
                    {(data?.rules ?? []).map((rule) => (
                      <Card key={rule.id} size="small" onClick={() => editExistingRule(rule)} className="inspector-rule">
                        <Typography.Text strong>{rule.name}</Typography.Text>
                        <div><Tag>{rule.action}</Tag><Tag>p{rule.priority}</Tag></div>
                      </Card>
                    ))}
                  </Space>
                </aside>
              </div>
            )
          },
          {
            key: "questions",
            label: "Questions",
            children: (
              <DndContext onDragEnd={onDragEnd}>
                <SortableContext items={questions.map((item) => item.id)} strategy={verticalListSortingStrategy}>
                  {questions.map((question) => (
                    <SortableQuestion
                      key={question.id}
                      question={question}
                      onEdit={openQuestionModal}
                      onDelete={(item) => deleteQuestion.mutate(item.id)}
                    />
                  ))}
                </SortableContext>
              </DndContext>
            )
          },
          {
            key: "rules",
            label: "Rules",
            children: (
              <Space direction="vertical" style={{ width: "100%" }}>
                {(data?.rules ?? []).map((rule) => (
                  <Card key={rule.id} onClick={() => editExistingRule(rule)}>
                    <Typography.Text strong>{rule.name}</Typography.Text>
                    <div><Tag>{rule.action}</Tag><Tag>priority {rule.priority}</Tag></div>
                  </Card>
                ))}
              </Space>
            )
          }
        ]}
      />

      <Modal
        title={editingQuestion ? "Edit question" : "Add question"}
        open={questionModalOpen}
        onCancel={() => setQuestionModalOpen(false)}
        footer={null}
        destroyOnClose
      >
        <Form form={questionForm} layout="vertical" onFinish={submitQuestion} preserve={false} initialValues={getInitialQuestionValues()}>
          <Form.Item name="title" label="Title" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="description" label="Description"><Input.TextArea rows={2} /></Form.Item>
          <Form.Item name="type" label="Type" rules={[{ required: true }]}>
            <Select options={QUESTION_TYPES.map((value) => ({ value }))} />
          </Form.Item>
          <Form.Item name="is_required" label="Required" valuePropName="checked"><Switch /></Form.Item>
          <Form.Item shouldUpdate={(prev, next) => prev.type !== next.type}>
            {({ getFieldValue }) => {
              const type = getFieldValue("type") as QuestionType;
              if (isChoiceQuestion(type)) {
                return (
                  <Form.List name="options">
                    {(fields, { add, remove }) => (
                      <Space direction="vertical" style={{ width: "100%" }}>
                        {fields.map((field) => (
                          <Space key={field.key} align="baseline">
                            <Form.Item {...field} name={[field.name, "label"]} rules={[{ required: true }]}><Input placeholder="Label" /></Form.Item>
                            <Form.Item {...field} name={[field.name, "value"]} rules={[{ required: true }]}><Input placeholder="Value" /></Form.Item>
                            <Button danger icon={<DeleteOutlined />} onClick={() => remove(field.name)} />
                          </Space>
                        ))}
                        <Button icon={<PlusOutlined />} onClick={() => add({ label: "", value: "", position: fields.length })}>Add option</Button>
                      </Space>
                    )}
                  </Form.List>
                );
              }
              if (type === "RATING") return <Form.Item name="max" label="Max score"><InputNumber min={2} max={20} /></Form.Item>;
              if (type === "MATRIX") {
                return (
                  <>
                    <Form.Item name="rowsText" label="Rows"><Input.TextArea rows={3} /></Form.Item>
                    <Form.Item name="columnsText" label="Columns"><Input.TextArea rows={2} /></Form.Item>
                  </>
                );
              }
              return null;
            }}
          </Form.Item>
          <Button type="primary" htmlType="submit" icon={<SaveOutlined />} loading={createQuestion.isPending || updateQuestion.isPending}>
            Save
          </Button>
        </Form>
      </Modal>

      <Modal
        title={editingRule ? "Edit branch" : "Create branch"}
        open={ruleModalOpen}
        onCancel={() => {
          setRuleModalOpen(false);
          setEditingRule(null);
        }}
        footer={null}
        destroyOnClose
      >
        <Form form={ruleForm} layout="vertical" onFinish={submitRule} preserve={false}>
          <Form.Item name="sourceQuestionId" label="Source question" rules={[{ required: true }]}>
            <Select options={questions.map((question) => ({ value: question.id, label: question.title }))} />
          </Form.Item>
          <Form.Item shouldUpdate={(prev, next) => prev.sourceQuestionId !== next.sourceQuestionId}>
            {({ getFieldValue }) => {
              const source = questions.find((question) => question.id === getFieldValue("sourceQuestionId"));
              return (
                <Form.Item name="sourceKey" label="Source answer field" rules={[{ required: true }]}>
                  <Select options={source ? getSourceFieldOptions(source) : []} />
                </Form.Item>
              );
            }}
          </Form.Item>
          <Form.Item name="operator" label="Operator" rules={[{ required: true }]}>
            <Select options={OPERATORS.map((value) => ({ value }))} />
          </Form.Item>
          <Form.Item name="value" label="Value" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="target_question_id" label="Target question" rules={[{ required: true }]}>
            <Select options={questions.map((question) => ({ value: question.id, label: question.title }))} />
          </Form.Item>
          <Form.Item name="action" label="Action" rules={[{ required: true }]}>
            <Select options={RULE_ACTIONS.map((value) => ({ value }))} />
          </Form.Item>
          <Form.Item name="priority" label="Priority" rules={[{ required: true }]}><InputNumber min={0} /></Form.Item>
          <Form.Item name="name" label="Rule name"><Input placeholder="Generated if left empty" /></Form.Item>
          <Space>
            <Button type="primary" htmlType="submit" icon={<SaveOutlined />} loading={createRule.isPending || updateRule.isPending}>Save branch</Button>
            {editingRule && (
              <Popconfirm title="Delete branch?" onConfirm={() => deleteRule.mutate(editingRule.id)}>
                <Button danger icon={<DeleteOutlined />}>Delete</Button>
              </Popconfirm>
            )}
          </Space>
        </Form>
      </Modal>
    </>
  );
}
