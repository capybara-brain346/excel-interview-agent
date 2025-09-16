import { Request, Response, NextFunction } from "express";
import { ValidationError } from "joi";
import { createLogger } from "@/utils/logger";
import { config } from "@/config/env";
import { ErrorResponse, CustomRequest, CustomResponse } from "@/types";

const logger = createLogger("ErrorMiddleware");

export class AppError extends Error {
  public statusCode: number;
  public isOperational: boolean;

  constructor(
    message: string,
    statusCode: number = 500,
    isOperational: boolean = true
  ) {
    super(message);
    this.statusCode = statusCode;
    this.isOperational = isOperational;

    Error.captureStackTrace(this, this.constructor);
  }
}

export const createError = (
  message: string,
  statusCode: number = 500
): AppError => {
  return new AppError(message, statusCode);
};

const handleJoiValidationError = (error: ValidationError): AppError => {
  const message = error.details.map((detail) => detail.message).join(", ");
  return new AppError(`Validation Error: ${message}`, 400);
};

const handleDatabaseError = (error: any): AppError => {
  if (error.code === "23505") {
    return new AppError("Duplicate entry found", 409);
  }
  if (error.code === "23503") {
    return new AppError("Referenced record not found", 404);
  }
  if (error.code === "23502") {
    return new AppError("Required field is missing", 400);
  }
  return new AppError("Database operation failed", 500);
};

const sendErrorResponse = (
  error: AppError,
  req: CustomRequest,
  res: CustomResponse
): void => {
  const errorResponse: ErrorResponse = {
    success: false,
    error: error.message,
    message: config.env === "production" ? "An error occurred" : error.message,
    statusCode: error.statusCode,
    timestamp: new Date().toISOString(),
    path: req.path || req.originalUrl,
  };

  if (config.env === "development") {
    errorResponse.stack = error.stack;
  }

  logger.error("Request error", error, {
    requestId: req.requestId,
    method: req.method,
    url: req.originalUrl,
    statusCode: error.statusCode,
    userAgent: req.get("User-Agent"),
    ip: req.ip,
  });

  res.status(error.statusCode).json(errorResponse);
};

export const errorHandler = (
  error: Error,
  req: CustomRequest,
  res: CustomResponse,
  _next: NextFunction
): void => {
  let appError = error as AppError;

  if (!(error instanceof AppError)) {
    if (error.name === "ValidationError") {
      appError = handleJoiValidationError(error as ValidationError);
    } else if (error.name === "DatabaseError" || (error as any).code) {
      appError = handleDatabaseError(error);
    } else {
      appError = new AppError(
        config.env === "production" ? "Internal server error" : error.message,
        500,
        false
      );
    }
  }

  sendErrorResponse(appError, req, res);
};

export const notFoundHandler = (
  req: CustomRequest,
  res: CustomResponse,
  _next: NextFunction
): void => {
  const error = new AppError(`Route ${req.originalUrl} not found`, 404);
  sendErrorResponse(error, req, res);
};

export const asyncHandler = (fn: Function) => {
  return (req: Request, res: Response, next: NextFunction) => {
    Promise.resolve(fn(req, res, next)).catch(next);
  };
};
