import "reflect-metadata";
import express from "express";
import cors from "cors";
import helmet from "helmet";
import compression from "compression";
import rateLimit from "express-rate-limit";
import { config } from "./config/env";
import { database } from "@/config/database";
import { createLogger } from "@/utils/logger";
import { requestLogger } from "@/middleware/request.middleware";
import { errorHandler, notFoundHandler } from "@/middleware/error.middleware";
import { apiRoutes } from "@/routes";

const logger = createLogger("Application");

class Application {
  private app: express.Application;
  private port: number;

  constructor() {
    this.app = express();
    this.port = config.port;
    this.initializeMiddlewares();
    this.initializeRoutes();
    this.initializeErrorHandling();
  }

  private initializeMiddlewares(): void {
    this.app.use(helmet());
    this.app.use(compression());

    const limiter = rateLimit({
      windowMs: config.rateLimit.windowMs,
      max: config.rateLimit.maxRequests,
      message: {
        success: false,
        error: "Too many requests from this IP",
        message: "Please try again later",
        statusCode: 429,
        timestamp: new Date().toISOString(),
      },
      standardHeaders: true,
      legacyHeaders: false,
    });

    this.app.use(limiter);

    this.app.use(
      cors({
        origin: config.cors.origin,
        credentials: true,
      })
    );

    this.app.use(express.json({ limit: "10mb" }));
    this.app.use(express.urlencoded({ extended: true, limit: "10mb" }));

    this.app.use(requestLogger);
  }

  private initializeRoutes(): void {
    this.app.get("/", (_req, res) => {
      res.json({
        success: true,
        message: "Excel Interview Agent Backend API",
        version: "1.0.0",
        timestamp: new Date().toISOString(),
        environment: config.env,
      });
    });

    this.app.use("/api", apiRoutes);
  }

  private initializeErrorHandling(): void {
    this.app.use(notFoundHandler);
    this.app.use(errorHandler);
  }

  private async connectDatabase(): Promise<void> {
    try {
      await database.connect();

      if (config.env !== "test") {
        await database.runMigrations();
        logger.info("Database migrations completed");
      }
    } catch (error) {
      logger.error("Failed to initialize database", error);
      throw error;
    }
  }

  public async start(): Promise<void> {
    try {
      await this.connectDatabase();

      const server = this.app.listen(this.port, () => {
        logger.info("Server started successfully", {
          port: this.port,
          environment: config.env,
          nodeVersion: process.version,
          pid: process.pid,
        });
      });

      const gracefulShutdown = (signal: string) => {
        logger.info(`Received ${signal}, shutting down gracefully`);

        server.close(async () => {
          logger.info("HTTP server closed");

          try {
            await database.disconnect();
            logger.info("Application shutdown complete");
            process.exit(0);
          } catch (error) {
            logger.error("Error during shutdown", error);
            process.exit(1);
          }
        });
      };

      process.on("SIGTERM", () => gracefulShutdown("SIGTERM"));
      process.on("SIGINT", () => gracefulShutdown("SIGINT"));

      process.on("unhandledRejection", (reason, promise) => {
        logger.error("Unhandled Promise Rejection", reason, { promise });
      });

      process.on("uncaughtException", (error) => {
        logger.error("Uncaught Exception", error);
        process.exit(1);
      });
    } catch (error) {
      logger.error("Failed to start application", error);
      process.exit(1);
    }
  }

  public getApp(): express.Application {
    return this.app;
  }
}

if (require.main === module) {
  const app = new Application();
  app.start().catch((error) => {
    console.error("Failed to start application:", error);
    process.exit(1);
  });
}

export default Application;
