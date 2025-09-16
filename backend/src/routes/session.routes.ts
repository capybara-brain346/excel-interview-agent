import { Router } from "express";
import { SessionController } from "@/controllers/session.controller";
import { asyncHandler } from "@/middleware/error.middleware";
import { validate, validateParams } from "@/middleware/validation.middleware";
import {
  createSessionSchema,
  submitResponseSchema,
  evaluateResponseSchema,
  uuidParamSchema,
  responseParamSchema,
  interviewParamSchema,
} from "@/utils/validation.schemas";

const router = Router();
const sessionController = new SessionController();

router.post(
  "/",
  validate(createSessionSchema),
  asyncHandler(sessionController.createSession.bind(sessionController))
);

router.get(
  "/:id",
  validateParams(uuidParamSchema),
  asyncHandler(sessionController.getSession.bind(sessionController))
);

router.post(
  "/:id/start",
  validateParams(uuidParamSchema),
  asyncHandler(sessionController.startSession.bind(sessionController))
);

router.post(
  "/:id/responses",
  validateParams(uuidParamSchema),
  validate(submitResponseSchema),
  asyncHandler(sessionController.submitResponse.bind(sessionController))
);

router.post(
  "/:id/complete",
  validateParams(uuidParamSchema),
  asyncHandler(sessionController.completeSession.bind(sessionController))
);

router.post(
  "/:id/abandon",
  validateParams(uuidParamSchema),
  asyncHandler(sessionController.abandonSession.bind(sessionController))
);

router.put(
  "/responses/:responseId/evaluate",
  validateParams(responseParamSchema),
  validate(evaluateResponseSchema),
  asyncHandler(sessionController.evaluateResponse.bind(sessionController))
);

router.get(
  "/interview/:interviewId",
  validateParams(interviewParamSchema),
  asyncHandler(sessionController.getSessionsByInterview.bind(sessionController))
);

export { router as sessionRoutes };
