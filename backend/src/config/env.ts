import Joi from "joi";
import { Environment, DatabaseConfig } from "@/types";

const envSchema = Joi.object({
  NODE_ENV: Joi.string()
    .valid("development", "production", "test")
    .default("development"),
  PORT: Joi.number().port().default(3001),

  DB_HOST: Joi.string().required(),
  DB_PORT: Joi.number().port().default(5432),
  DB_NAME: Joi.string().required(),
  DB_USER: Joi.string().required(),
  DB_PASSWORD: Joi.string().required(),
  DB_SSL: Joi.boolean().default(false),
  DB_POOL_MIN: Joi.number().min(1).default(2),
  DB_POOL_MAX: Joi.number().min(1).default(10),

  LOG_LEVEL: Joi.string()
    .valid("error", "warn", "info", "debug")
    .default("info"),
  LOG_FILE_MAX_SIZE: Joi.string().default("20m"),
  LOG_FILE_MAX_FILES: Joi.string().default("14d"),

  RATE_LIMIT_WINDOW_MS: Joi.number().default(900000),
  RATE_LIMIT_MAX_REQUESTS: Joi.number().default(100),

  JWT_SECRET: Joi.string().min(32).required(),
  JWT_EXPIRES_IN: Joi.string().default("24h"),

  CORS_ORIGIN: Joi.string().uri().default("http://localhost:3000"),
}).unknown();

const { error, value: envVars } = envSchema.validate(process.env);

if (error) {
  throw new Error(`Environment validation error: ${error.message}`);
}

export interface Config {
  env: Environment;
  port: number;
  database: DatabaseConfig;
  logging: {
    level: string;
    fileMaxSize: string;
    fileMaxFiles: string;
  };
  rateLimit: {
    windowMs: number;
    maxRequests: number;
  };
  jwt: {
    secret: string;
    expiresIn: string;
  };
  cors: {
    origin: string;
  };
}

export const config: Config = {
  env: envVars.NODE_ENV as Environment,
  port: envVars.PORT as number,
  database: {
    host: envVars.DB_HOST as string,
    port: envVars.DB_PORT as number,
    database: envVars.DB_NAME as string,
    user: envVars.DB_USER as string,
    password: envVars.DB_PASSWORD as string,
    ssl: envVars.DB_SSL as boolean,
    pool: {
      min: envVars.DB_POOL_MIN as number,
      max: envVars.DB_POOL_MAX as number,
    },
  },
  logging: {
    level: envVars.LOG_LEVEL as string,
    fileMaxSize: envVars.LOG_FILE_MAX_SIZE as string,
    fileMaxFiles: envVars.LOG_FILE_MAX_FILES as string,
  },
  rateLimit: {
    windowMs: envVars.RATE_LIMIT_WINDOW_MS as number,
    maxRequests: envVars.RATE_LIMIT_MAX_REQUESTS as number,
  },
  jwt: {
    secret: envVars.JWT_SECRET as string,
    expiresIn: envVars.JWT_EXPIRES_IN as string,
  },
  cors: {
    origin: envVars.CORS_ORIGIN as string,
  },
};
