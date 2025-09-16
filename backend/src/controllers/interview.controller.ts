import { Response } from "express";
import { InterviewService } from "@/services/interview.service";
import { CustomRequest, ApiResponse } from "@/types";
import { createLogger } from "@/utils/logger";
import { AppError } from "@/middleware/error.middleware";

const logger = createLogger("InterviewController");
const interviewService = new InterviewService();

export class InterviewController {
  async createInterview(req: CustomRequest, res: Response): Promise<void> {
    const interview = await interviewService.createInterview(req.body);

    const response: ApiResponse = {
      success: true,
      data: interview,
      message: "Interview created successfully",
      timestamp: new Date().toISOString(),
    };

    logger.info("Interview created via API", {
      interviewId: interview.id,
      requestId: req.requestId,
    });

    res.status(201).json(response);
  }

  async getInterview(req: CustomRequest, res: Response): Promise<void> {
    const { id } = req.params;
    const interview = await interviewService.getInterviewById(id!);

    if (!interview) {
      throw new AppError("Interview not found", 404);
    }

    const response: ApiResponse = {
      success: true,
      data: interview,
      timestamp: new Date().toISOString(),
    };

    res.json(response);
  }

  async getInterviews(req: CustomRequest, res: Response): Promise<void> {
    const { page, limit, sortBy, sortOrder } = req.query;

    const paginationParams = {
      page: page ? parseInt(page as string, 10) : 1,
      limit: limit ? parseInt(limit as string, 10) : 10,
      sortBy: sortBy as string,
      sortOrder: sortOrder as "asc" | "desc",
    };

    const result = await interviewService.getInterviews(paginationParams);

    const response: ApiResponse = {
      success: true,
      data: result,
      timestamp: new Date().toISOString(),
    };

    res.json(response);
  }

  async updateInterview(req: CustomRequest, res: Response): Promise<void> {
    const { id } = req.params;
    const interview = await interviewService.updateInterview(id!, req.body);

    if (!interview) {
      throw new AppError("Interview not found", 404);
    }

    const response: ApiResponse = {
      success: true,
      data: interview,
      message: "Interview updated successfully",
      timestamp: new Date().toISOString(),
    };

    logger.info("Interview updated via API", {
      interviewId: id,
      requestId: req.requestId,
    });

    res.json(response);
  }

  async deleteInterview(req: CustomRequest, res: Response): Promise<void> {
    const { id } = req.params;
    const success = await interviewService.deleteInterview(id!);

    if (!success) {
      throw new AppError("Interview not found", 404);
    }

    const response: ApiResponse = {
      success: true,
      message: "Interview deleted successfully",
      timestamp: new Date().toISOString(),
    };

    logger.info("Interview deleted via API", {
      interviewId: id,
      requestId: req.requestId,
    });

    res.json(response);
  }

  async addQuestion(req: CustomRequest, res: Response): Promise<void> {
    const { id } = req.params;
    const question = await interviewService.addQuestionToInterview(
      id!,
      req.body
    );

    const response: ApiResponse = {
      success: true,
      data: question,
      message: "Question added successfully",
      timestamp: new Date().toISOString(),
    };

    logger.info("Question added to interview via API", {
      interviewId: id,
      questionId: question.id,
      requestId: req.requestId,
    });

    res.status(201).json(response);
  }

  async updateQuestion(req: CustomRequest, res: Response): Promise<void> {
    const { questionId } = req.params;
    const question = await interviewService.updateQuestion(
      questionId!,
      req.body
    );

    if (!question) {
      throw new AppError("Question not found", 404);
    }

    const response: ApiResponse = {
      success: true,
      data: question,
      message: "Question updated successfully",
      timestamp: new Date().toISOString(),
    };

    logger.info("Question updated via API", {
      questionId,
      requestId: req.requestId,
    });

    res.json(response);
  }

  async deleteQuestion(req: CustomRequest, res: Response): Promise<void> {
    const { questionId } = req.params;
    const success = await interviewService.deleteQuestion(questionId!);

    if (!success) {
      throw new AppError("Question not found", 404);
    }

    const response: ApiResponse = {
      success: true,
      message: "Question deleted successfully",
      timestamp: new Date().toISOString(),
    };

    logger.info("Question deleted via API", {
      questionId,
      requestId: req.requestId,
    });

    res.json(response);
  }
}
