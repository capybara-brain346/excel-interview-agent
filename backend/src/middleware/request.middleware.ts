import { Request, Response, NextFunction } from "express";
import { v4 as uuidv4 } from "uuid";
import { createLogger } from "@/utils/logger";
import { CustomRequest, CustomResponse } from "@/types";

const logger = createLogger("RequestMiddleware");

export const requestLogger = (
  req: CustomRequest,
  res: CustomResponse,
  next: NextFunction
): void => {
  const requestId = uuidv4();
  const startTime = Date.now();

  req.requestId = requestId;
  req.startTime = startTime;
  res.locals.requestId = requestId;

  logger.info("Incoming request", {
    requestId,
    method: req.method,
    url: req.originalUrl,
    userAgent: req.get("User-Agent"),
    ip: req.ip,
    body: req.method !== "GET" ? req.body : undefined,
  });

  const originalSend = res.send;
  res.send = function (body) {
    const duration = Date.now() - startTime;

    logger.info("Request completed", {
      requestId,
      method: req.method,
      url: req.originalUrl,
      statusCode: res.statusCode,
      duration: `${duration}ms`,
      contentLength: res.get("Content-Length") || body?.length || 0,
    });

    return originalSend.call(this, body);
  };

  next();
};

export const healthCheck = (_req: Request, res: Response): void => {
  res.status(200).json({
    success: true,
    message: "Server is healthy",
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    version: process.env.npm_package_version || "1.0.0",
  });
};
