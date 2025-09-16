import { Repository } from "typeorm";
import { database } from "@/config/database";
import { createLogger } from "@/utils/logger";
import { AppError } from "@/middleware/error.middleware";
import { SessionStatus } from "@/types";
import { InterviewSession, SessionResponse } from "@/entities";

const logger = createLogger("SessionService");

export class SessionService {
  private get sessionRepository(): Repository<InterviewSession> {
    return database.dataSource.getRepository(InterviewSession);
  }

  private get responseRepository(): Repository<SessionResponse> {
    return database.dataSource.getRepository(SessionResponse);
  }

  async createSession(data: {
    interview_id: string;
    candidate_name: string;
    candidate_email: string;
  }): Promise<InterviewSession> {
    try {
      const session = this.sessionRepository.create({
        ...data,
        status: SessionStatus.PENDING,
      });
      const savedSession = await this.sessionRepository.save(session);

      logger.info("Interview session created", { sessionId: savedSession.id });
      savedSession.responses = [];
      return savedSession;
    } catch (error) {
      logger.error("Failed to create session", error);
      throw new AppError("Failed to create interview session", 500);
    }
  }

  async getSessionById(id: string): Promise<InterviewSession | null> {
    try {
      const session = await this.sessionRepository.findOne({
        where: { id },
        relations: ["responses"],
        order: {
          responses: {
            created_at: "ASC",
          },
        },
      });

      return session;
    } catch (error) {
      logger.error("Failed to get session", error, { sessionId: id });
      throw new AppError("Failed to retrieve session", 500);
    }
  }

  async startSession(sessionId: string): Promise<InterviewSession | null> {
    try {
      await this.sessionRepository.update(sessionId, {
        status: SessionStatus.IN_PROGRESS,
        started_at: new Date(),
      });

      const session = await this.sessionRepository.findOne({
        where: { id: sessionId },
        relations: ["responses"],
        order: {
          responses: {
            created_at: "ASC",
          },
        },
      });

      if (session) {
        logger.info("Interview session started", { sessionId });
      }

      return session;
    } catch (error) {
      logger.error("Failed to start session", error, { sessionId });
      throw new AppError("Failed to start session", 500);
    }
  }

  async submitResponse(data: {
    session_id: string;
    question_id: string;
    answer: string;
    time_taken: number;
  }): Promise<SessionResponse> {
    try {
      const response = this.responseRepository.create({
        ...data,
        is_correct: false,
      });
      const savedResponse = await this.responseRepository.save(response);

      logger.info("Response submitted", {
        sessionId: data.session_id,
        questionId: data.question_id,
        responseId: savedResponse.id,
      });

      return savedResponse;
    } catch (error) {
      logger.error("Failed to submit response", error);
      throw new AppError("Failed to submit response", 500);
    }
  }

  async evaluateResponse(
    responseId: string,
    score: number,
    isCorrect: boolean
  ): Promise<SessionResponse | null> {
    try {
      await this.responseRepository.update(responseId, {
        score,
        is_correct: isCorrect,
      });

      const response = await this.responseRepository.findOne({
        where: { id: responseId },
      });

      if (response) {
        logger.info("Response evaluated", { responseId, score, isCorrect });
      }

      return response;
    } catch (error) {
      logger.error("Failed to evaluate response", error, { responseId });
      throw new AppError("Failed to evaluate response", 500);
    }
  }

  async completeSession(sessionId: string): Promise<InterviewSession | null> {
    try {
      const responses = await this.responseRepository.find({
        where: {
          session_id: sessionId,
        },
      });

      const scoredResponses = responses.filter(
        (r) => r.score !== null && r.score !== undefined
      );
      const totalScore = scoredResponses.reduce(
        (sum, response) => sum + (response.score || 0),
        0
      );

      await this.sessionRepository.update(sessionId, {
        status: SessionStatus.COMPLETED,
        completed_at: new Date(),
        total_score: totalScore,
      });

      const session = await this.sessionRepository.findOne({
        where: { id: sessionId },
        relations: ["responses"],
        order: {
          responses: {
            created_at: "ASC",
          },
        },
      });

      if (session) {
        logger.info("Interview session completed", { sessionId, totalScore });
      }

      return session;
    } catch (error) {
      logger.error("Failed to complete session", error, { sessionId });
      throw new AppError("Failed to complete session", 500);
    }
  }

  async getSessionsByInterview(
    interviewId: string
  ): Promise<InterviewSession[]> {
    try {
      const sessions = await this.sessionRepository.find({
        where: { interview_id: interviewId },
        relations: ["responses"],
        order: {
          created_at: "DESC",
          responses: {
            created_at: "ASC",
          },
        },
      });

      return sessions;
    } catch (error) {
      logger.error("Failed to get sessions by interview", error, {
        interviewId,
      });
      throw new AppError("Failed to retrieve sessions", 500);
    }
  }

  async abandonSession(sessionId: string): Promise<InterviewSession | null> {
    try {
      await this.sessionRepository.update(sessionId, {
        status: SessionStatus.ABANDONED,
      });

      const session = await this.sessionRepository.findOne({
        where: { id: sessionId },
        relations: ["responses"],
        order: {
          responses: {
            created_at: "ASC",
          },
        },
      });

      if (session) {
        logger.info("Interview session abandoned", { sessionId });
      }

      return session;
    } catch (error) {
      logger.error("Failed to abandon session", error, { sessionId });
      throw new AppError("Failed to abandon session", 500);
    }
  }
}
