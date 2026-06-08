export type Role = "HR" | "EMPLOYEE";
export type SurveyStatus = "DRAFT" | "PUBLISHED" | "CLOSED" | "ARCHIVED";
export type QuestionType = "SINGLE_CHOICE" | "MULTIPLE_CHOICE" | "RATING" | "TEXT" | "MATRIX";
export type BranchOperator = "equals" | "lte" | "gte" | "in";

export interface BlueprintPosition {
  x: number;
  y: number;
}

export interface QuestionBlueprintSettings {
  position?: BlueprintPosition;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
}

export interface Survey {
  id: string;
  title: string;
  description: string | null;
  status: SurveyStatus;
  is_anonymous: boolean;
  estimated_minutes: number;
  ends_at: string | null;
}

export interface QuestionOption {
  id?: string;
  label: string;
  value: string;
  position: number;
}

export interface Question {
  id: string;
  survey_id: string;
  title: string;
  description: string | null;
  type: QuestionType;
  position: number;
  is_required: boolean;
  settings: Record<string, unknown> & { blueprint?: QuestionBlueprintSettings };
  options: QuestionOption[];
}

export interface SurveyDetail extends Survey {
  questions: Question[];
  rules: SurveyRule[];
}

export interface SurveyRule {
  id: string;
  target_question_id: string;
  name: string;
  priority: number;
  action: "SHOW_QUESTION" | "HIDE_QUESTION";
  condition: Record<string, unknown>;
}

export interface EmployeeSurveyCard extends Survey {
  assignment_status: "PENDING" | "STARTED" | "SUBMITTED" | null;
  anonymity_notice: string;
  completion_percent: number;
}
