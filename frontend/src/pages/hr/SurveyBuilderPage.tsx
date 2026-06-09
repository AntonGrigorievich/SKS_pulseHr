import {
  DeleteOutlined,
  EditOutlined,
  EyeInvisibleOutlined,
  LinkOutlined,
  PlusOutlined,
  SaveOutlined
} from "@ant-design/icons";
import { DndContext, DragEndEvent } from "@dnd-kit/core";
import { SortableContext, arrayMove, useSortable, verticalListSortingStrategy } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Background,
  Controls,
  Handle,
  MarkerType,
  MiniMap,
  Position,
  ReactFlow,
  applyNodeChanges,
  type Connection,
  type Edge,
  type IsValidConnection,
  type Node,
  type NodeChange,
  type NodeProps
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
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
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import { apiRequest } from "../../api/client";
import {
  BlueprintPosition,
  BranchOperator,
  Question,
  QuestionOption,
  QuestionType,
  Survey,
  SurveyDetail,
  SurveyRule
} from "../../api/types";

const QUESTION_TYPES: QuestionType[] = ["SINGLE_CHOICE", "MULTIPLE_CHOICE", "RATING", "TEXT", "MATRIX"];
const RULE_ACTIONS = ["SHOW_QUESTION", "HIDE_QUESTION"] as const;
const OPERATORS: BranchOperator[] = ["equals", "lte", "gte", "in"];
const ALWAYS_CONDITION = "always";
const ALWAYS_OUTPUT_KEY = "__always__";
const ALWAYS_OUTPUT_VALUE = "__always__";
const NODE_WIDTH = 300;
const TARGET_HANDLE_ID = "question-input";
const FLOW_FIT_VIEW_OPTIONS = { padding: 0.24 };
const FLOW_SNAP_GRID: [number, number] = [20, 20];

type RuleAction = (typeof RULE_ACTIONS)[number];
type RuleConditionOperator = BranchOperator | typeof ALWAYS_CONDITION;
type QuestionOutput = {
  key: string;
  label: string;
  value: string | number;
  kind?: "always" | "answer";
};
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
  sourceKey?: string;
  sourceValue?: string | number;
  targetQuestionId: string;
  operator?: RuleConditionOperator;
};
type RuleFormValues = {
  sourceQuestionId: string;
  sourceKey?: string;
  target_question_id: string;
  operator: RuleConditionOperator;
  value?: string | number | Array<string | number> | boolean;
  action: RuleAction;
  priority: number;
  name?: string;
};
type ParsedRule = {
  field?: string;
  sourceQuestionId: string;
  sourceKey?: string;
  operator: RuleConditionOperator;
  value?: unknown;
  isAlways: boolean;
};
type QuestionNodeData = {
  question: Question;
  outputs: QuestionOutput[];
  version: string;
  onEdit: (question: Question) => void;
  onDelete: (question: Question) => void;
};
type QuestionFlowNode = Node<QuestionNodeData, "question">;
type RuleEdgeData = {
  rule: SurveyRule;
  parsed: ParsedRule;
};
type RuleFlowEdge = Edge<RuleEdgeData, "smoothstep">;

function getQuestionSettings(question?: Pick<Question, "settings"> | null): Question["settings"] {
  return question?.settings ?? {};
}

function getQuestionOptions(question?: Pick<Question, "options"> | null): QuestionOption[] {
  return question?.options ?? [];
}

function getQuestionNodeVersion(question: Question) {
  return JSON.stringify({
    id: question.id,
    title: question.title,
    description: question.description,
    type: question.type,
    position: question.position,
    is_required: question.is_required,
    settings: getQuestionSettings(question),
    options: getQuestionOptions(question).map(({ id, label, value, position }) => ({ id, label, value, position }))
  });
}

function flowNodesMatch(currentNodes: QuestionFlowNode[], nextNodes: QuestionFlowNode[]) {
  if (currentNodes.length !== nextNodes.length) return false;
  return currentNodes.every((currentNode, index) => {
    const nextNode = nextNodes[index];
    return (
      currentNode.id === nextNode.id &&
      currentNode.type === nextNode.type &&
      currentNode.data.version === nextNode.data.version &&
      currentNode.position.x === nextNode.position.x &&
      currentNode.position.y === nextNode.position.y &&
      currentNode.selected === nextNode.selected
    );
  });
}

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

function QuestionFlowCard({ data, selected }: NodeProps<QuestionFlowNode>) {
  return (
    <div className={`rule-node-card ${selected ? "rule-node-card-selected" : ""}`}>
      <Handle id={TARGET_HANDLE_ID} type="target" position={Position.Left} className="rule-node-handle rule-node-input-handle" />
      <div className="rule-node-header">
        <div className="rule-node-title">
          <Typography.Text strong ellipsis title={data.question.title}>
            {data.question.title}
          </Typography.Text>
          <div className="rule-node-tags">
            <Tag>{data.question.type}</Tag>
            {data.question.is_required && <Tag color="red">required</Tag>}
          </div>
        </div>
        <Space size={4} className="nodrag">
          <Button size="small" icon={<EditOutlined />} onClick={() => data.onEdit(data.question)} />
          <Popconfirm title="Delete question?" onConfirm={() => data.onDelete(data.question)}>
            <Button size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      </div>
      <div className="rule-node-outputs">
        {data.outputs.map((output) => (
          <div
            key={encodeOutputHandle(output)}
            className={`rule-node-output ${output.kind === "always" ? "rule-node-output-always" : ""}`}
          >
            <span>{output.label}</span>
            <Handle
              id={encodeOutputHandle(output)}
              type="source"
              position={Position.Right}
              className="rule-node-handle rule-node-output-handle"
            />
          </div>
        ))}
      </div>
    </div>
  );
}

const nodeTypes = { question: QuestionFlowCard };

function isChoiceQuestion(question: Question | QuestionType) {
  const type = typeof question === "string" ? question : question.type;
  return type === "SINGLE_CHOICE" || type === "MULTIPLE_CHOICE";
}

function getBlueprintPosition(question: Question, index: number): BlueprintPosition {
  const blueprint = getQuestionSettings(question).blueprint as { position?: Partial<BlueprintPosition> } | undefined;
  const saved = blueprint?.position;
  if (typeof saved?.x === "number" && typeof saved?.y === "number") return { x: saved.x, y: saved.y };
  return { x: 40 + (index % 3) * 360, y: 40 + Math.floor(index / 3) * 260 };
}

function buildSettings(values: QuestionFormValues, existing?: Question): Record<string, unknown> {
  const settings = { ...getQuestionSettings(existing) };
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

function getAlwaysOutput(): QuestionOutput {
  return { key: ALWAYS_OUTPUT_KEY, label: "Always", value: ALWAYS_OUTPUT_VALUE, kind: "always" };
}

function getAnswerOutputs(question: Question): QuestionOutput[] {
  if (question.type === "SINGLE_CHOICE") return getQuestionOptions(question).map((option) => ({ key: "option", label: option.label, value: option.value }));
  if (question.type === "MULTIPLE_CHOICE") return getQuestionOptions(question).map((option) => ({ key: "options", label: option.label, value: option.value }));
  if (question.type === "RATING") return [{ key: "score", label: "Score", value: "" }];
  if (question.type === "MATRIX") return ((getQuestionSettings(question).rows as string[] | undefined) ?? []).map((row) => ({ key: `rows.${row}`, label: row, value: "" }));
  return [{ key: "text", label: "Text", value: "" }];
}

function getOutputKeys(question: Question): QuestionOutput[] {
  return [getAlwaysOutput(), ...getAnswerOutputs(question)];
}

function getSourceFieldOptions(question: Question) {
  if (question.type === "SINGLE_CHOICE") return [{ value: "option", label: "Selected option" }];
  if (question.type === "MULTIPLE_CHOICE") return [{ value: "options", label: "Selected options" }];
  if (question.type === "RATING") return [{ value: "score", label: "Rating score" }];
  if (question.type === "TEXT") return [{ value: "text", label: "Text response" }];
  const labels = new Map<string, string>();
  for (const output of getAnswerOutputs(question)) {
    if (!labels.has(output.key)) labels.set(output.key, output.label);
  }
  return [...labels.entries()].map(([value, label]) => ({ value, label }));
}

function getValueOptions(question: Question | undefined, sourceKey: string | undefined) {
  if (!question || !sourceKey) return [];
  if (isChoiceQuestion(question)) {
    return getQuestionOptions(question).map((option) => ({ value: option.value, label: option.label }));
  }
  if (question.type === "MATRIX" && sourceKey.startsWith("rows.")) {
    const columns = (getQuestionSettings(question).columns as string[] | undefined) ?? ["1", "2", "3", "4", "5"];
    return columns.map((column) => ({ value: column, label: column }));
  }
  return [];
}

function getDefaultSourceKey(question: Question | undefined) {
  return question ? (getAnswerOutputs(question)[0]?.key ?? getSourceFieldOptions(question)[0]?.value ?? "text") : "text";
}

function getDefaultOperator(question: Question | undefined): BranchOperator {
  if (question?.type === "RATING") return "gte";
  return "equals";
}

function getDefaultRuleValue(question: Question | undefined, sourceKey: string | undefined, sourceValue?: string | number, operator: RuleConditionOperator = "equals") {
  if (operator === ALWAYS_CONDITION) return true;
  if (operator === "in") return sourceValue ? [sourceValue] : [];
  if (sourceValue !== undefined && sourceValue !== "") return sourceValue;
  if (question?.type === "RATING") return 1;
  const valueOption = getValueOptions(question, sourceKey)[0];
  return valueOption?.value ?? "";
}

function encodeOutputHandle(output: QuestionOutput) {
  return `out:${encodeURIComponent(JSON.stringify([output.key, output.value ?? ""]))}`;
}

function decodeOutputHandle(handleId?: string | null): Pick<ConnectionDraft, "sourceKey" | "sourceValue"> | null {
  if (!handleId?.startsWith("out:")) return null;
  try {
    const parsed = JSON.parse(decodeURIComponent(handleId.slice(4))) as [string, string | number];
    return { sourceKey: parsed[0], sourceValue: parsed[1] };
  } catch {
    return null;
  }
}

function getRuleSourceHandle(question: Question, parsed: ParsedRule) {
  if (parsed.isAlways) return encodeOutputHandle(getAlwaysOutput());
  const outputs = getAnswerOutputs(question);
  const sourceKey = parsed.sourceKey ?? getDefaultSourceKey(question);
  const exactOutput = outputs.find((output) => output.key === parsed.sourceKey && valuesMatch(output.value, parsed.value));
  const fieldOutput = outputs.find((output) => output.key === sourceKey);
  return encodeOutputHandle(exactOutput ?? fieldOutput ?? { key: sourceKey, label: sourceKey, value: "" });
}

function buildField(questionId: string, key: string) {
  return `answers.${questionId}.${key}`;
}

function normalizeRuleValue(operator: RuleConditionOperator, value: RuleFormValues["value"]) {
  if (operator === ALWAYS_CONDITION) return true;
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
  const sourceQuestionId = rule.condition.source_question_id;
  const isAlwaysCondition = rule.condition.mode === ALWAYS_CONDITION || rule.condition.op === "ALWAYS";
  if (isAlwaysCondition && typeof sourceQuestionId === "string") {
    return {
      sourceQuestionId,
      sourceKey: ALWAYS_OUTPUT_KEY,
      operator: ALWAYS_CONDITION,
      value: true,
      isAlways: true
    };
  }
  const condition = conditions.find((item) => typeof item.field === "string" && String(item.field).startsWith("answers."));
  if (!condition || typeof condition.field !== "string" || typeof condition.operator !== "string") return null;
  const [, conditionSourceQuestionId, ...keyParts] = condition.field.split(".");
  if (!conditionSourceQuestionId || keyParts.length === 0) return null;
  if (!OPERATORS.includes(condition.operator as BranchOperator)) return null;
  return {
    field: condition.field,
    sourceQuestionId: conditionSourceQuestionId,
    sourceKey: keyParts.join("."),
    operator: condition.operator as BranchOperator,
    value: condition.value,
    isAlways: false
  };
}

function actionLabel(action: RuleAction) {
  return action === "SHOW_QUESTION" ? "Show" : "Hide";
}

function operatorLabel(operator: RuleConditionOperator) {
  if (operator === ALWAYS_CONDITION) return "always";
  if (operator === "equals") return "is";
  if (operator === "in") return "is one of";
  if (operator === "gte") return "is at least";
  return "is at most";
}

function formatRuleValue(value: unknown) {
  if (Array.isArray(value)) return value.join(", ");
  if (value === undefined || value === null || value === "") return "blank";
  return String(value);
}

function formatRuleName(questions: Question[], values: RuleFormValues) {
  const source = questions.find((question) => question.id === values.sourceQuestionId);
  const target = questions.find((question) => question.id === values.target_question_id);
  if (values.operator === ALWAYS_CONDITION) return `${actionLabel(values.action)} "${target?.title ?? "target"}" after "${source?.title ?? "source"}"`;
  return `${actionLabel(values.action)} "${target?.title ?? "target"}" when "${source?.title ?? "source"}" ${operatorLabel(values.operator)} "${formatRuleValue(values.value)}"`;
}

function formatEdgeLabel(rule: SurveyRule, parsed: ParsedRule) {
  if (parsed.isAlways) return `${actionLabel(rule.action)} always`;
  return `${actionLabel(rule.action)} if ${operatorLabel(parsed.operator)} ${formatRuleValue(parsed.value)}`;
}

function formatRuleSummary(questions: Question[], rule: SurveyRule) {
  const parsed = parseRule(rule);
  if (!parsed) return rule.name;
  const source = questions.find((question) => question.id === parsed.sourceQuestionId);
  const target = questions.find((question) => question.id === rule.target_question_id);
  if (parsed.isAlways) return `${actionLabel(rule.action)} "${target?.title ?? "target"}" after "${source?.title ?? "source"}"`;
  return `${actionLabel(rule.action)} "${target?.title ?? "target"}" when "${source?.title ?? "source"}" ${operatorLabel(parsed.operator)} ${formatRuleValue(parsed.value)}`;
}

function getInitialQuestionValues(question?: Question): Partial<QuestionFormValues> {
  const settings = getQuestionSettings(question);
  return {
    title: question?.title ?? "",
    description: question?.description ?? "",
    type: question?.type ?? "TEXT",
    is_required: question?.is_required ?? true,
    options: getQuestionOptions(question).length ? getQuestionOptions(question) : [{ label: "Yes", value: "yes", position: 0 }],
    max: Number(settings.max ?? 10),
    rowsText: ((settings.rows as string[] | undefined) ?? []).join("\n"),
    columnsText: ((settings.columns as string[] | undefined) ?? ["1", "2", "3", "4", "5"]).join("\n")
  };
}

export function SurveyBuilderPage() {
  const { surveyId } = useParams();
  const [questionModalOpen, setQuestionModalOpen] = useState(false);
  const [editingQuestion, setEditingQuestion] = useState<Question | null>(null);
  const [ruleModalOpen, setRuleModalOpen] = useState(false);
  const [editingRule, setEditingRule] = useState<SurveyRule | null>(null);
  const [connectionDraft, setConnectionDraft] = useState<ConnectionDraft | null>(null);
  const [flowNodes, setFlowNodes] = useState<QuestionFlowNode[]>([]);
  const [selectedRuleId, setSelectedRuleId] = useState<string | null>(null);
  const [questionForm] = Form.useForm<QuestionFormValues>();
  const [ruleForm] = Form.useForm<RuleFormValues>();
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

  const invalidateSurvey = () => queryClient.invalidateQueries({ queryKey: ["survey-detail", surveyId] });
  const createQuestion = useMutation({
    mutationFn: (payload: Record<string, unknown>) =>
      apiRequest<Question>(`/surveys/${surveyId}/questions`, { method: "POST", body: JSON.stringify(payload) }),
    onSuccess: (question) => {
      setQuestionModalOpen(false);
      setEditingQuestion(null);
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
  const makeAnonymous = useMutation({
    mutationFn: () =>
      apiRequest<Survey>(`/surveys/${surveyId}`, { method: "PATCH", body: JSON.stringify({ is_anonymous: true }) }),
    onSuccess: () => {
      message.success("Survey is anonymous");
      invalidateSurvey();
    }
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
      setConnectionDraft(null);
      invalidateSurvey();
    }
  });
  const deleteRule = useMutation({
    mutationFn: (id: string) => apiRequest(`/rules/${id}`, { method: "DELETE" }),
    onSuccess: () => {
      setRuleModalOpen(false);
      setEditingRule(null);
      setConnectionDraft(null);
      invalidateSurvey();
    }
  });

  const deleteQuestionMutateRef = useRef(deleteQuestion.mutate);
  const updateQuestionMutateRef = useRef(updateQuestion.mutate);
  deleteQuestionMutateRef.current = deleteQuestion.mutate;
  updateQuestionMutateRef.current = updateQuestion.mutate;

  const openQuestionModal = useCallback((question?: Question) => {
    setEditingQuestion(question ?? null);
    questionForm.setFieldsValue(getInitialQuestionValues(question));
    setQuestionModalOpen(true);
  }, [questionForm]);

  const deleteQuestionFromFlow = useCallback((question: Question) => {
    deleteQuestionMutateRef.current(question.id);
  }, []);

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

  const baseFlowNodes = useMemo<QuestionFlowNode[]>(
    () =>
      questions.map((question, index) => ({
        id: question.id,
        type: "question",
        position: getBlueprintPosition(question, index),
        data: {
          question,
          outputs: getOutputKeys(question),
          version: getQuestionNodeVersion(question),
          onEdit: openQuestionModal,
          onDelete: deleteQuestionFromFlow
        },
        width: NODE_WIDTH
      })),
    [questions, openQuestionModal, deleteQuestionFromFlow]
  );

  const flowEdges = useMemo<RuleFlowEdge[]>(
    () =>
      parsedRules.flatMap(({ rule, parsed }) => {
        if (!parsed) return [];
        const source = questions.find((question) => question.id === parsed.sourceQuestionId);
        const target = questions.find((question) => question.id === rule.target_question_id);
        if (!source || !target) return [];
        const isShowRule = rule.action === "SHOW_QUESTION";
        return [
          {
            id: rule.id,
            source: parsed.sourceQuestionId,
            sourceHandle: getRuleSourceHandle(source, parsed),
            target: rule.target_question_id,
            targetHandle: TARGET_HANDLE_ID,
            type: "smoothstep",
            label: formatEdgeLabel(rule, parsed),
            selected: selectedRuleId === rule.id,
            markerEnd: { type: MarkerType.ArrowClosed },
            data: { rule, parsed },
            className: isShowRule ? "rule-edge rule-edge-show" : "rule-edge rule-edge-hide",
            style: { stroke: isShowRule ? "#287a4b" : "#b42318", strokeWidth: selectedRuleId === rule.id ? 3 : 2 },
            labelBgPadding: [8, 4],
            labelBgBorderRadius: 4,
            labelBgStyle: { fill: "#ffffff", stroke: isShowRule ? "#b7dfc6" : "#f4b8b2" },
            labelStyle: { fill: "#1f2937", fontSize: 12, fontWeight: 600 }
          }
        ];
      }),
    [parsedRules, questions, selectedRuleId]
  );

  useEffect(() => {
    setFlowNodes((currentNodes) => {
      const currentNodesById = new Map(currentNodes.map((node) => [node.id, node]));
      const nextNodes = baseFlowNodes.map((node) => ({
        ...node,
        position: currentNodesById.get(node.id)?.position ?? node.position,
        selected: currentNodesById.get(node.id)?.selected
      }));
      return flowNodesMatch(currentNodes, nextNodes) ? currentNodes : nextNodes;
    });
  }, [baseFlowNodes]);

  const onNodesChange = useCallback((changes: NodeChange<QuestionFlowNode>[]) => {
    setFlowNodes((nodes) => applyNodeChanges(changes, nodes));
  }, []);

  const onNodeDragStop = useCallback(
    (_event: MouseEvent | TouchEvent, node: QuestionFlowNode) => {
      const question = questions.find((item) => item.id === node.id);
      if (!question) return;
      const position = {
        x: Math.max(0, Math.round(node.position.x)),
        y: Math.max(0, Math.round(node.position.y))
      };
      updateQuestionMutateRef.current({ id: question.id, payload: { settings: withBlueprintPosition(getQuestionSettings(question), position) } });
    },
    [questions]
  );

  const isValidRuleConnection = useCallback<IsValidConnection<RuleFlowEdge>>(
    (connection) => Boolean(connection.source && connection.target && connection.source !== connection.target),
    []
  );

  const clearSelectedRule = useCallback(() => {
    setSelectedRuleId(null);
  }, []);

  function openDefaultRuleModal() {
    const source = questions[0];
    const target = questions.find((question) => question.id !== source?.id);
    if (!source || !target) {
      message.info("Add at least two questions before creating a rule");
      return;
    }
    const output = getAlwaysOutput();
    openRuleModal({
      sourceQuestionId: source.id,
      sourceKey: output.key,
      sourceValue: output.value,
      targetQuestionId: target.id,
      operator: ALWAYS_CONDITION
    });
  }

  function handleConnect(connection: Connection) {
    if (!connection.source || !connection.target) return;
    const source = questions.find((question) => question.id === connection.source);
    const decoded = decodeOutputHandle(connection.sourceHandle);
    const fallbackOutput = source ? getOutputKeys(source)[0] : undefined;
    if (!source || (!decoded && !fallbackOutput)) {
      message.error("Choose an answer output before connecting a rule");
      return;
    }
    const sourceKey = decoded?.sourceKey ?? fallbackOutput?.key;
    openRuleModal({
      sourceQuestionId: connection.source,
      sourceKey: sourceKey ?? getDefaultSourceKey(source),
      sourceValue: decoded?.sourceValue ?? fallbackOutput?.value,
      targetQuestionId: connection.target,
      operator: sourceKey === ALWAYS_OUTPUT_KEY ? ALWAYS_CONDITION : undefined
    });
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
    const parsed = rule ? parseRule(rule) : null;
    const operator = parsed?.operator ?? draft.operator ?? (draft.sourceKey === ALWAYS_OUTPUT_KEY ? ALWAYS_CONDITION : getDefaultOperator(source));
    const sourceKey = operator === ALWAYS_CONDITION ? ALWAYS_OUTPUT_KEY : draft.sourceKey ?? getDefaultSourceKey(source);
    setEditingRule(rule ?? null);
    setConnectionDraft(draft);
    ruleForm.setFieldsValue({
      sourceQuestionId: draft.sourceQuestionId,
      sourceKey,
      target_question_id: draft.targetQuestionId,
      operator,
      value: (parsed?.value as RuleFormValues["value"] | undefined) ?? getDefaultRuleValue(source, sourceKey, output?.value ?? draft.sourceValue, operator),
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
    const isAlwaysRule = values.operator === ALWAYS_CONDITION;
    const field = isAlwaysRule ? undefined : buildField(values.sourceQuestionId, values.sourceKey ?? getDefaultSourceKey(questions.find((question) => question.id === values.sourceQuestionId)));
    const ruleValue = normalizeRuleValue(values.operator, values.value);
    const duplicate = (data?.rules ?? []).find((rule) => {
      if (editingRule?.id === rule.id) return false;
      const parsed = parseRule(rule);
      if (isAlwaysRule) {
        return (
          parsed?.isAlways &&
          parsed.sourceQuestionId === values.sourceQuestionId &&
          rule.target_question_id === values.target_question_id &&
          rule.action === values.action
        );
      }
      if (!parsed) return false;
      return (
        parsed.field === field &&
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
      condition: isAlwaysRule
        ? { op: "AND", mode: ALWAYS_CONDITION, source_question_id: values.sourceQuestionId, conditions: [] }
        : { op: "AND", conditions: [{ field, operator: values.operator, value: ruleValue }] }
    };
    if (editingRule) updateRule.mutate({ id: editingRule.id, payload });
    else createRule.mutate(payload);
  }

  function editExistingRule(rule: SurveyRule) {
    const parsed = parseRule(rule);
    if (!parsed) return;
    setSelectedRuleId(rule.id);
    openRuleModal(
      { sourceQuestionId: parsed.sourceQuestionId, sourceKey: parsed.sourceKey, targetQuestionId: rule.target_question_id, operator: parsed.operator },
      rule
    );
  }

  return (
    <>
      <div className="toolbar">
        <div>
          <Typography.Title level={2} style={{ margin: 0 }}>{data?.title}</Typography.Title>
          <Space size={8}>
            <Typography.Text type="secondary">Survey builder</Typography.Text>
            {data?.is_anonymous && <Tag color="green">Anonymous</Tag>}
          </Space>
        </div>
        <Space>
          <Button
            icon={<EyeInvisibleOutlined />}
            onClick={() => makeAnonymous.mutate()}
            loading={makeAnonymous.isPending}
            disabled={!surveyId || data?.is_anonymous}
          >
            Make anon
          </Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => openQuestionModal()}>Add question</Button>
        </Space>
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
                    <Button icon={<LinkOutlined />} onClick={openDefaultRuleModal} disabled={questions.length < 2}>Add rule</Button>
                  </Space>
                  <Typography.Text type="secondary">{questions.length} questions / {(data?.rules ?? []).length} rules</Typography.Text>
                </div>
                <div className="blueprint-workspace">
                  <ReactFlow<QuestionFlowNode, RuleFlowEdge>
                    nodes={flowNodes}
                    edges={flowEdges}
                    nodeTypes={nodeTypes}
                    onNodesChange={onNodesChange}
                    onNodeDragStop={onNodeDragStop}
                    onConnect={handleConnect}
                    onEdgeClick={(event, edge) => {
                      event.stopPropagation();
                      if (edge.data?.rule) editExistingRule(edge.data.rule);
                    }}
                    onPaneClick={clearSelectedRule}
                    isValidConnection={isValidRuleConnection}
                    fitView
                    fitViewOptions={FLOW_FIT_VIEW_OPTIONS}
                    minZoom={0.35}
                    maxZoom={1.4}
                    snapToGrid
                    snapGrid={FLOW_SNAP_GRID}
                    nodesDraggable
                    nodesConnectable
                    elementsSelectable
                  >
                    <Background gap={20} color="#d8e2ef" />
                    <Controls position="bottom-left" />
                    <MiniMap nodeColor="#d9e9f7" nodeStrokeColor="#4f6f8f" pannable zoomable />
                  </ReactFlow>
                </div>
                <aside className="blueprint-inspector">
                  <Typography.Title level={5}>Rules</Typography.Title>
                  <Space direction="vertical" style={{ width: "100%" }}>
                    {(data?.rules ?? []).length === 0 && <Typography.Text type="secondary">No rules yet</Typography.Text>}
                    {(data?.rules ?? []).map((rule) => (
                      <Card
                        key={rule.id}
                        size="small"
                        onClick={() => editExistingRule(rule)}
                        className={`inspector-rule ${selectedRuleId === rule.id ? "inspector-rule-selected" : ""}`}
                      >
                        <Typography.Text strong>{formatRuleSummary(questions, rule)}</Typography.Text>
                        <div className="inspector-rule-tags">
                          <Tag color={rule.action === "SHOW_QUESTION" ? "green" : "red"}>{actionLabel(rule.action)}</Tag>
                          <Tag>p{rule.priority}</Tag>
                        </div>
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
                    <Typography.Text strong>{formatRuleSummary(questions, rule)}</Typography.Text>
                    <div><Tag color={rule.action === "SHOW_QUESTION" ? "green" : "red"}>{actionLabel(rule.action)}</Tag><Tag>priority {rule.priority}</Tag></div>
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
        title={editingRule ? "Edit rule" : "Create rule"}
        open={ruleModalOpen}
        onCancel={() => {
          setRuleModalOpen(false);
          setEditingRule(null);
          setConnectionDraft(null);
        }}
        footer={null}
        destroyOnClose
      >
        <Form form={ruleForm} layout="vertical" onFinish={submitRule} preserve={false}>
          <Form.Item name="sourceQuestionId" label="When question" rules={[{ required: true }]}>
            <Select
              showSearch
              optionFilterProp="label"
              options={questions.map((question) => ({ value: question.id, label: question.title }))}
              onChange={(questionId) => {
                const source = questions.find((question) => question.id === questionId);
                const currentOperator = (ruleForm.getFieldValue("operator") as RuleConditionOperator | undefined) ?? ALWAYS_CONDITION;
                const operator = currentOperator === ALWAYS_CONDITION ? ALWAYS_CONDITION : getDefaultOperator(source);
                const output = operator === ALWAYS_CONDITION ? getAlwaysOutput() : source ? getAnswerOutputs(source)[0] : undefined;
                const sourceKey = operator === ALWAYS_CONDITION ? ALWAYS_OUTPUT_KEY : output?.key ?? getDefaultSourceKey(source);
                ruleForm.setFieldsValue({
                  sourceKey,
                  operator,
                  value: getDefaultRuleValue(source, sourceKey, output?.value, operator)
                });
              }}
            />
          </Form.Item>
          <Form.Item shouldUpdate={(prev, next) => prev.sourceQuestionId !== next.sourceQuestionId || prev.operator !== next.operator}>
            {({ getFieldValue }) => {
              const operator = (getFieldValue("operator") as RuleConditionOperator | undefined) ?? ALWAYS_CONDITION;
              if (operator === ALWAYS_CONDITION) return null;
              const source = questions.find((question) => question.id === getFieldValue("sourceQuestionId"));
              return (
                <Form.Item name="sourceKey" label="Answer field" rules={[{ required: true }]}>
                  <Select
                    options={source ? getSourceFieldOptions(source) : []}
                    onChange={(sourceKey) => {
                      const operator = (ruleForm.getFieldValue("operator") as RuleConditionOperator | undefined) ?? getDefaultOperator(source);
                      ruleForm.setFieldsValue({ value: getDefaultRuleValue(source, sourceKey, undefined, operator) });
                    }}
                  />
                </Form.Item>
              );
            }}
          </Form.Item>
          <Form.Item name="operator" label="Condition" rules={[{ required: true }]}>
            <Select
              options={[
                { value: ALWAYS_CONDITION, label: "No rule (always true)" },
                ...OPERATORS.map((value) => ({ value, label: operatorLabel(value) }))
              ]}
              onChange={(operator: RuleConditionOperator) => {
                const source = questions.find((question) => question.id === ruleForm.getFieldValue("sourceQuestionId"));
                if (operator === ALWAYS_CONDITION) {
                  ruleForm.setFieldsValue({ sourceKey: ALWAYS_OUTPUT_KEY, value: true });
                  return;
                }
                const value = ruleForm.getFieldValue("value") as RuleFormValues["value"] | undefined;
                const currentSourceKey = ruleForm.getFieldValue("sourceKey") as string | undefined;
                const sourceKey = currentSourceKey && currentSourceKey !== ALWAYS_OUTPUT_KEY ? currentSourceKey : getDefaultSourceKey(source);
                if (operator === "in" && value !== undefined && !Array.isArray(value)) {
                  ruleForm.setFieldsValue({ sourceKey, value: typeof value === "boolean" || value === "" ? [] : [value] });
                  return;
                }
                if (operator !== "in" && Array.isArray(value)) {
                  ruleForm.setFieldsValue({ sourceKey, value: value[0] ?? getDefaultRuleValue(source, sourceKey, undefined, operator) });
                  return;
                }
                ruleForm.setFieldsValue({ sourceKey, value: value === true ? getDefaultRuleValue(source, sourceKey, undefined, operator) : value });
              }}
            />
          </Form.Item>
          <Form.Item shouldUpdate={(prev, next) => prev.sourceQuestionId !== next.sourceQuestionId || prev.sourceKey !== next.sourceKey || prev.operator !== next.operator}>
            {({ getFieldValue }) => {
              const source = questions.find((question) => question.id === getFieldValue("sourceQuestionId"));
              const sourceKey = getFieldValue("sourceKey") as string | undefined;
              const operator = (getFieldValue("operator") as RuleConditionOperator | undefined) ?? ALWAYS_CONDITION;
              if (operator === ALWAYS_CONDITION) return null;
              const valueOptions = getValueOptions(source, sourceKey);
              if (operator === "in" && valueOptions.length > 0) {
                return (
                  <Form.Item name="value" label="Answer value" rules={[{ required: true }]}>
                    <Select mode="multiple" options={valueOptions} />
                  </Form.Item>
                );
              }
              if (valueOptions.length > 0) {
                return (
                  <Form.Item name="value" label="Answer value" rules={[{ required: true }]}>
                    <Select options={valueOptions} />
                  </Form.Item>
                );
              }
              if (source?.type === "RATING" && operator !== "in") {
                return (
                  <Form.Item name="value" label="Answer value" rules={[{ required: true }]}>
                    <InputNumber min={0} max={Number(getQuestionSettings(source).max ?? 10)} style={{ width: "100%" }} />
                  </Form.Item>
                );
              }
              return (
                <Form.Item name="value" label="Answer value" rules={[{ required: true }]}>
                  <Input />
                </Form.Item>
              );
            }}
          </Form.Item>
          <Form.Item name="target_question_id" label="Then question" rules={[{ required: true }]}>
            <Select showSearch optionFilterProp="label" options={questions.map((question) => ({ value: question.id, label: question.title }))} />
          </Form.Item>
          <Form.Item name="action" label="Action" rules={[{ required: true }]}>
            <Select options={RULE_ACTIONS.map((value) => ({ value, label: `${actionLabel(value)} question` }))} />
          </Form.Item>
          <Form.Item name="priority" label="Priority" rules={[{ required: true }]}><InputNumber min={0} /></Form.Item>
          <Form.Item name="name" label="Rule name"><Input placeholder="Generated if left empty" /></Form.Item>
          <Space>
            <Button type="primary" htmlType="submit" icon={<SaveOutlined />} loading={createRule.isPending || updateRule.isPending}>Save rule</Button>
            {editingRule && (
              <Popconfirm title="Delete rule?" onConfirm={() => deleteRule.mutate(editingRule.id)}>
                <Button danger icon={<DeleteOutlined />}>Delete</Button>
              </Popconfirm>
            )}
          </Space>
        </Form>
      </Modal>
    </>
  );
}
