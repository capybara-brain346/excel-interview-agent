import winston from "winston";
import DailyRotateFile from "winston-daily-rotate-file";
import { config } from "@/config/env";

const logFormat = winston.format.combine(
  winston.format.timestamp({ format: "YYYY-MM-DD HH:mm:ss" }),
  winston.format.errors({ stack: true }),
  winston.format.json()
);

const consoleFormat = winston.format.combine(
  winston.format.timestamp({ format: "YYYY-MM-DD HH:mm:ss" }),
  winston.format.errors({ stack: true }),
  winston.format.colorize(),
  winston.format.printf(({ timestamp, level, message, stack, ...meta }) => {
    let log = `${timestamp} [${level}]: ${message}`;
    if (stack) {
      log += `\n${stack}`;
    }
    if (Object.keys(meta).length > 0) {
      log += `\n${JSON.stringify(meta, null, 2)}`;
    }
    return log;
  })
);

const transports: winston.transport[] = [
  new winston.transports.Console({
    format: consoleFormat,
    level: config.logging.level,
  }),
];

if (config.env !== "test") {
  transports.push(
    new DailyRotateFile({
      filename: "logs/application-%DATE%.log",
      datePattern: "YYYY-MM-DD",
      maxSize: config.logging.fileMaxSize,
      maxFiles: config.logging.fileMaxFiles,
      format: logFormat,
      level: "info",
    })
  );

  transports.push(
    new DailyRotateFile({
      filename: "logs/error-%DATE%.log",
      datePattern: "YYYY-MM-DD",
      maxSize: config.logging.fileMaxSize,
      maxFiles: config.logging.fileMaxFiles,
      format: logFormat,
      level: "error",
    })
  );
}

export const logger = winston.createLogger({
  level: config.logging.level,
  format: logFormat,
  transports,
  exitOnError: false,
});

export class Logger {
  private context: string;

  constructor(context: string) {
    this.context = context;
  }

  private formatMessage(message: string, meta?: any): [string, any] {
    const formattedMessage = `[${this.context}] ${message}`;
    const formattedMeta = meta
      ? { context: this.context, ...meta }
      : { context: this.context };
    return [formattedMessage, formattedMeta];
  }

  debug(message: string, meta?: any): void {
    const [formattedMessage, formattedMeta] = this.formatMessage(message, meta);
    logger.debug(formattedMessage, formattedMeta);
  }

  info(message: string, meta?: any): void {
    const [formattedMessage, formattedMeta] = this.formatMessage(message, meta);
    logger.info(formattedMessage, formattedMeta);
  }

  warn(message: string, meta?: any): void {
    const [formattedMessage, formattedMeta] = this.formatMessage(message, meta);
    logger.warn(formattedMessage, formattedMeta);
  }

  error(message: string, error?: Error | any, meta?: any): void {
    const [formattedMessage, formattedMeta] = this.formatMessage(message, {
      error:
        error instanceof Error
          ? { message: error.message, stack: error.stack }
          : error,
      ...meta,
    });
    logger.error(formattedMessage, formattedMeta);
  }
}

export const createLogger = (context: string): Logger => new Logger(context);
