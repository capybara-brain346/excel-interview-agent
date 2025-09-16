import { BaseEntity } from "./common.types";

export interface Interview extends BaseEntity {
  title: string;
  description?: string;
  difficulty_level: DifficultyLevel;
  estimated_duration: number;
  status: InterviewStatus;
  questions: InterviewQuestion[];
}

export interface InterviewQuestion extends BaseEntity {
  interview_id: string;
  question_text: string;
  question_type: QuestionType;
  expected_answer?: string;
  points: number;
  order_index: number;
  excel_scenario?: ExcelScenario;
}

export interface ExcelScenario {
  data_setup: string;
  required_formulas?: string[];
  expected_output: string;
  hints?: string[];
}

export interface InterviewSession extends BaseEntity {
  interview_id: string;
  candidate_name: string;
  candidate_email: string;
  status: SessionStatus;
  started_at?: Date;
  completed_at?: Date;
  total_score?: number;
  responses: SessionResponse[];
}

export interface SessionResponse extends BaseEntity {
  session_id: string;
  question_id: string;
  answer: string;
  score?: number;
  time_taken: number;
  is_correct: boolean;
}

export enum DifficultyLevel {
  BEGINNER = "beginner",
  INTERMEDIATE = "intermediate",
  ADVANCED = "advanced",
  EXPERT = "expert",
}

export enum InterviewStatus {
  DRAFT = "draft",
  ACTIVE = "active",
  ARCHIVED = "archived",
}

export enum QuestionType {
  MULTIPLE_CHOICE = "multiple_choice",
  TEXT_INPUT = "text_input",
  FORMULA = "formula",
  PRACTICAL = "practical",
}

export enum SessionStatus {
  PENDING = "pending",
  IN_PROGRESS = "in_progress",
  COMPLETED = "completed",
  ABANDONED = "abandoned",
}
