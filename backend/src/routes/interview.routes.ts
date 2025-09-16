import { Router } from "express";
import { InterviewController } from "@/controllers/interview.controller";
import { asyncHandler } from "@/middleware/error.middleware";
import {
  validate,
  validateQuery,
  validateParams,
} from "@/middleware/validation.middleware";
import {
  createInterviewSchema,
  updateInterviewSchema,
  createQuestionSchema,
  updateQuestionSchema,
  paginationQuerySchema,
  uuidParamSchema,
  questionParamSchema,
} from "@/utils/validation.schemas";

const router = Router();
const interviewController = new InterviewController();

router.post(
  "/",
  validate(createInterviewSchema),
  asyncHandler(interviewController.createInterview.bind(interviewController))
);

router.get(
  "/",
  validateQuery(paginationQuerySchema),
  asyncHandler(interviewController.getInterviews.bind(interviewController))
);

router.get(
  "/:id",
  validateParams(uuidParamSchema),
  asyncHandler(interviewController.getInterview.bind(interviewController))
);

router.put(
  "/:id",
  validateParams(uuidParamSchema),
  validate(updateInterviewSchema),
  asyncHandler(interviewController.updateInterview.bind(interviewController))
);

router.delete(
  "/:id",
  validateParams(uuidParamSchema),
  asyncHandler(interviewController.deleteInterview.bind(interviewController))
);

router.post(
  "/:id/questions",
  validateParams(uuidParamSchema),
  validate(createQuestionSchema),
  asyncHandler(interviewController.addQuestion.bind(interviewController))
);

router.put(
  "/questions/:questionId",
  validateParams(questionParamSchema),
  validate(updateQuestionSchema),
  asyncHandler(interviewController.updateQuestion.bind(interviewController))
);

router.delete(
  "/questions/:questionId",
  validateParams(questionParamSchema),
  asyncHandler(interviewController.deleteQuestion.bind(interviewController))
);

export { router as interviewRoutes };
