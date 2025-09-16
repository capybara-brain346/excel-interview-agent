import { Router } from "express";
import { interviewRoutes } from "./interview.routes";
import { sessionRoutes } from "./session.routes";
import { healthCheck } from "@/middleware/request.middleware";

const router = Router();

router.get("/health", healthCheck);

router.use("/interviews", interviewRoutes);
router.use("/sessions", sessionRoutes);

export { router as apiRoutes };
