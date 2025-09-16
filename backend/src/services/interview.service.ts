import { Repository } from "typeorm";
import { database } from "@/config/database";
import { createLogger } from "@/utils/logger";
import { AppError } from "@/middleware/error.middleware";
import { PaginationParams, PaginatedResponse } from "@/types";
import { Interview, InterviewQuestion } from "@/entities";

const logger = createLogger("InterviewService");

export class InterviewService {
  private get interviewRepository(): Repository<Interview> {
    return database.dataSource.getRepository(Interview);
  }

  private get questionRepository(): Repository<InterviewQuestion> {
    return database.dataSource.getRepository(InterviewQuestion);
  }

  async createInterview(
    data: Omit<
      Interview,
      "id" | "created_at" | "updated_at" | "questions" | "sessions"
    >
  ): Promise<Interview> {
    try {
      const interview = this.interviewRepository.create(data);
      const savedInterview = await this.interviewRepository.save(interview);

      logger.info("Interview created", { interviewId: savedInterview.id });
      savedInterview.questions = [];
      return savedInterview;
    } catch (error) {
      logger.error("Failed to create interview", error);
      throw new AppError("Failed to create interview", 500);
    }
  }

  async getInterviewById(id: string): Promise<Interview | null> {
    try {
      const interview = await this.interviewRepository.findOne({
        where: { id },
        relations: ["questions"],
        order: {
          questions: {
            order_index: "ASC",
          },
        },
      });

      return interview;
    } catch (error) {
      logger.error("Failed to get interview", error, { interviewId: id });
      throw new AppError("Failed to retrieve interview", 500);
    }
  }

  async getInterviews(
    params: PaginationParams = {}
  ): Promise<PaginatedResponse<Interview>> {
    try {
      const {
        page = 1,
        limit = 10,
        sortBy = "created_at",
        sortOrder = "desc",
      } = params;
      const skip = (page - 1) * limit;

      const [interviews, total] = await this.interviewRepository.findAndCount({
        relations: ["questions"],
        order: {
          [sortBy]: sortOrder.toUpperCase() as "ASC" | "DESC",
          questions: {
            order_index: "ASC",
          },
        },
        skip,
        take: limit,
      });

      const totalPages = Math.ceil(total / limit);

      return {
        data: interviews,
        pagination: {
          page,
          limit,
          total,
          totalPages,
          hasNext: page < totalPages,
          hasPrev: page > 1,
        },
      };
    } catch (error) {
      logger.error("Failed to get interviews", error);
      throw new AppError("Failed to retrieve interviews", 500);
    }
  }

  async updateInterview(
    id: string,
    data: Partial<Interview>
  ): Promise<Interview | null> {
    try {
      await this.interviewRepository.update(id, data);
      const updatedInterview = await this.interviewRepository.findOne({
        where: { id },
        relations: ["questions"],
        order: {
          questions: {
            order_index: "ASC",
          },
        },
      });

      if (updatedInterview) {
        logger.info("Interview updated", { interviewId: id });
      }

      return updatedInterview;
    } catch (error) {
      logger.error("Failed to update interview", error, { interviewId: id });
      throw new AppError("Failed to update interview", 500);
    }
  }

  async deleteInterview(id: string): Promise<boolean> {
    try {
      const result = await this.interviewRepository.delete(id);
      const success = (result.affected ?? 0) > 0;

      if (success) {
        logger.info("Interview deleted", { interviewId: id });
      }

      return success;
    } catch (error) {
      logger.error("Failed to delete interview", error, { interviewId: id });
      throw new AppError("Failed to delete interview", 500);
    }
  }

  async addQuestionToInterview(
    interviewId: string,
    questionData: Omit<
      InterviewQuestion,
      | "id"
      | "created_at"
      | "updated_at"
      | "interview_id"
      | "interview"
      | "responses"
    >
  ): Promise<InterviewQuestion> {
    try {
      const question = this.questionRepository.create({
        ...questionData,
        interview_id: interviewId,
      });
      const savedQuestion = await this.questionRepository.save(question);

      logger.info("Question added to interview", {
        interviewId,
        questionId: savedQuestion.id,
      });
      return savedQuestion;
    } catch (error) {
      logger.error("Failed to add question to interview", error, {
        interviewId,
      });
      throw new AppError("Failed to add question to interview", 500);
    }
  }

  async updateQuestion(
    questionId: string,
    data: Partial<InterviewQuestion>
  ): Promise<InterviewQuestion | null> {
    try {
      await this.questionRepository.update(questionId, data);
      const updatedQuestion = await this.questionRepository.findOne({
        where: { id: questionId },
      });

      if (updatedQuestion) {
        logger.info("Question updated", { questionId });
      }

      return updatedQuestion;
    } catch (error) {
      logger.error("Failed to update question", error, { questionId });
      throw new AppError("Failed to update question", 500);
    }
  }

  async deleteQuestion(questionId: string): Promise<boolean> {
    try {
      const result = await this.questionRepository.delete(questionId);
      const success = (result.affected ?? 0) > 0;

      if (success) {
        logger.info("Question deleted", { questionId });
      }

      return success;
    } catch (error) {
      logger.error("Failed to delete question", error, { questionId });
      throw new AppError("Failed to delete question", 500);
    }
  }
}
