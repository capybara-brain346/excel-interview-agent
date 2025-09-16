import Joi from "joi";

export const createInterviewSchema = Joi.object({
  title: Joi.string().min(1).max(255).required(),
  description: Joi.string().optional().allow(""),
  difficulty_level: Joi.string()
    .valid("beginner", "intermediate", "advanced", "expert")
    .required(),
  estimated_duration: Joi.number().integer().min(1).max(480).required(),
  status: Joi.string().valid("draft", "active", "archived").optional(),
});

export const updateInterviewSchema = Joi.object({
  title: Joi.string().min(1).max(255).optional(),
  description: Joi.string().optional().allow(""),
  difficulty_level: Joi.string()
    .valid("beginner", "intermediate", "advanced", "expert")
    .optional(),
  estimated_duration: Joi.number().integer().min(1).max(480).optional(),
  status: Joi.string().valid("draft", "active", "archived").optional(),
});

export const createQuestionSchema = Joi.object({
  question_text: Joi.string().min(1).required(),
  question_type: Joi.string()
    .valid("multiple_choice", "text_input", "formula", "practical")
    .required(),
  expected_answer: Joi.string().optional().allow(""),
  points: Joi.number().integer().min(1).max(100).default(1),
  order_index: Joi.number().integer().min(1).required(),
  excel_scenario: Joi.object({
    data_setup: Joi.string().required(),
    required_formulas: Joi.array().items(Joi.string()).optional(),
    expected_output: Joi.string().required(),
    hints: Joi.array().items(Joi.string()).optional(),
  }).optional(),
});

export const updateQuestionSchema = Joi.object({
  question_text: Joi.string().min(1).optional(),
  question_type: Joi.string()
    .valid("multiple_choice", "text_input", "formula", "practical")
    .optional(),
  expected_answer: Joi.string().optional().allow(""),
  points: Joi.number().integer().min(1).max(100).optional(),
  order_index: Joi.number().integer().min(1).optional(),
  excel_scenario: Joi.object({
    data_setup: Joi.string().required(),
    required_formulas: Joi.array().items(Joi.string()).optional(),
    expected_output: Joi.string().required(),
    hints: Joi.array().items(Joi.string()).optional(),
  }).optional(),
});

export const createSessionSchema = Joi.object({
  interview_id: Joi.string().uuid().required(),
  candidate_name: Joi.string().min(1).max(255).required(),
  candidate_email: Joi.string().email().required(),
});

export const submitResponseSchema = Joi.object({
  question_id: Joi.string().uuid().required(),
  answer: Joi.string().min(1).required(),
  time_taken: Joi.number().integer().min(0).required(),
});

export const evaluateResponseSchema = Joi.object({
  score: Joi.number().min(0).max(100).required(),
  is_correct: Joi.boolean().required(),
});

export const paginationQuerySchema = Joi.object({
  page: Joi.number().integer().min(1).optional(),
  limit: Joi.number().integer().min(1).max(100).optional(),
  sortBy: Joi.string().optional(),
  sortOrder: Joi.string().valid("asc", "desc").optional(),
});

export const uuidParamSchema = Joi.object({
  id: Joi.string().uuid().required(),
});

export const questionParamSchema = Joi.object({
  questionId: Joi.string().uuid().required(),
});

export const responseParamSchema = Joi.object({
  responseId: Joi.string().uuid().required(),
});

export const interviewParamSchema = Joi.object({
  interviewId: Joi.string().uuid().required(),
});
