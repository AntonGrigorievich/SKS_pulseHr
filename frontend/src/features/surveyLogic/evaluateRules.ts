import { Question, SurveyRule } from "../../api/types";

type Answers = Record<string, Record<string, unknown>>;

function readPath(source: Record<string, unknown>, path: string): unknown {
  return path.split(".").reduce<unknown>((value, key) => {
    if (value && typeof value === "object") {
      return (value as Record<string, unknown>)[key];
    }
    return undefined;
  }, source);
}

function compare(actual: unknown, operator: string, expected: unknown): boolean {
  if (operator === "equals") return Array.isArray(actual) ? actual.includes(expected) : actual === expected;
  if (operator === "lte") return Number(actual) <= Number(expected);
  if (operator === "gte") return Number(actual) >= Number(expected);
  if (operator === "in") {
    if (Array.isArray(actual) && Array.isArray(expected)) return actual.some((item) => expected.includes(item));
    if (Array.isArray(actual)) return actual.includes(expected);
    if (Array.isArray(expected)) return expected.includes(actual);
  }
  return false;
}

function evaluate(condition: Record<string, unknown>, context: Record<string, unknown>): boolean {
  const op = condition.op;
  const conditions = (condition.conditions as Record<string, unknown>[] | undefined) ?? [];
  if (op === "AND") return conditions.every((item) => evaluate(item, context));
  if (op === "OR") return conditions.some((item) => evaluate(item, context));
  if (op === "NOT") return !evaluate(conditions[0] ?? {}, context);

  const field = condition.field;
  const operator = condition.operator;
  if (typeof field !== "string" || typeof operator !== "string") return false;
  return compare(readPath(context, field), operator, condition.value);
}

export function visibleQuestions(questions: Question[], rules: SurveyRule[], answers: Answers): Question[] {
  const hidden = new Set<string>();
  const explicitlyShown = new Set<string>();
  const context = { answers };

  for (const rule of [...rules].sort((a, b) => a.priority - b.priority)) {
    if (!evaluate(rule.condition, context)) continue;
    if (rule.action === "HIDE_QUESTION") hidden.add(rule.target_question_id);
    if (rule.action === "SHOW_QUESTION") explicitlyShown.add(rule.target_question_id);
  }

  return questions
    .filter((question) => !hidden.has(question.id))
    .filter((question) => {
      const showRules = rules.filter((rule) => rule.action === "SHOW_QUESTION" && rule.target_question_id === question.id);
      return showRules.length === 0 || explicitlyShown.has(question.id);
    })
    .sort((a, b) => a.position - b.position);
}
