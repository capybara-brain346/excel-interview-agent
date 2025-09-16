import { Response } from "express";
import { SessionService } from "@/services/session.service";
import { CustomRequest, ApiResponse } from "@/types";
import { createLogger } from "@/utils/logger";
import { AppError } from "@/middleware/error.middleware";

const logger = createLogger("SessionController");
const sessionService = new SessionService();

export class SessionController {
  async createSession(req: CustomRequest, res: Response): Promise<void> {
    const session = await sessionService.createSession(req.body);

    const response: ApiResponse = {
      success: true,
      data: session,
      message: "Interview session created successfully",
      timestamp: new Date().toISOString(),
    };

    logger.info("Session created via API", {
      sessionId: session.id,
      requestId: req.requestId,
    });

    res.status(201).json(response);
  }

  async getSession(req: CustomRequest, res: Response): Promise<void> {
    const { id } = req.params;
    const session = await sessionService.getSessionById(id!);

    if (!session) {
      throw new AppError("Session not found", 404);
    }

    const response: ApiResponse = {
      success: true,
      data: session,
      timestamp: new Date().toISOString(),
    };

    res.json(response);
  }

  async startSession(req: CustomRequest, res: Response): Promise<void> {
    const { id } = req.params;
    const session = await sessionService.startSession(id!);

    if (!session) {
      throw new AppError("Session not found", 404);
    }

    const response: ApiResponse = {
      success: true,
      data: session,
      message: "Session started successfully",
      timestamp: new Date().toISOString(),
    };

    logger.info("Session started via API", {
      sessionId: id,
      requestId: req.requestId,
    });

    res.json(response);
  }

  async submitResponse(req: CustomRequest, res: Response): Promise<void> {
    const { id } = req.params;
    const responseData = await sessionService.submitResponse({
      session_id: id!,
      ...req.body,
    });

    const response: ApiResponse = {
      success: true,
      data: responseData,
      message: "Response submitted successfully",
      timestamp: new Date().toISOString(),
    };

    logger.info("Response submitted via API", {
      sessionId: id,
      responseId: responseData.id,
      requestId: req.requestId,
    });

    res.status(201).json(response);
  }

  async evaluateResponse(req: CustomRequest, res: Response): Promise<void> {
    const { responseId } = req.params;
    const { score, is_correct } = req.body;

    const responseData = await sessionService.evaluateResponse(
      responseId!,
      score,
      is_correct
    );

    if (!responseData) {
      throw new AppError("Response not found", 404);
    }

    const response: ApiResponse = {
      success: true,
      data: responseData,
      message: "Response evaluated successfully",
      timestamp: new Date().toISOString(),
    };

    logger.info("Response evaluated via API", {
      responseId,
      score,
      isCorrect: is_correct,
      requestId: req.requestId,
    });

    res.json(response);
  }

  async completeSession(req: CustomRequest, res: Response): Promise<void> {
    const { id } = req.params;
    const session = await sessionService.completeSession(id!);

    if (!session) {
      throw new AppError("Session not found", 404);
    }

    const response: ApiResponse = {
      success: true,
      data: session,
      message: "Session completed successfully",
      timestamp: new Date().toISOString(),
    };

    logger.info("Session completed via API", {
      sessionId: id,
      totalScore: session.total_score,
      requestId: req.requestId,
    });

    res.json(response);
  }

  async getSessionsByInterview(
    req: CustomRequest,
    res: Response
  ): Promise<void> {
    const { interviewId } = req.params;
    const sessions = await sessionService.getSessionsByInterview(interviewId!);

    const response: ApiResponse = {
      success: true,
      data: sessions,
      timestamp: new Date().toISOString(),
    };

    res.json(response);
  }

  async abandonSession(req: CustomRequest, res: Response): Promise<void> {
    const { id } = req.params;
    const session = await sessionService.abandonSession(id!);

    if (!session) {
      throw new AppError("Session not found", 404);
    }

    const response: ApiResponse = {
      success: true,
      data: session,
      message: "Session abandoned",
      timestamp: new Date().toISOString(),
    };

    logger.info("Session abandoned via API", {
      sessionId: id,
      requestId: req.requestId,
    });

    res.json(response);
  }
}
