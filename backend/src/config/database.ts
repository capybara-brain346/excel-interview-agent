import "reflect-metadata";
import { DataSource, DataSourceOptions } from "typeorm";
import { config } from "./env";
import { createLogger } from "@/utils/logger";
import {
  Interview,
  InterviewQuestion,
  InterviewSession,
  SessionResponse,
} from "@/entities";

const logger = createLogger("Database");

const baseConfig: DataSourceOptions = {
  type: "postgres",
  host: config.database.host,
  port: config.database.port,
  username: config.database.user,
  password: config.database.password,
  database: config.database.database,
  ssl: config.database.ssl ? { rejectUnauthorized: false } : false,
  entities: [Interview, InterviewQuestion, InterviewSession, SessionResponse],
  synchronize: false, // Always use migrations in production
  logging: config.env === "development" ? ["query", "error"] : ["error"],
  maxQueryExecutionTime: 5000, // Log slow queries
};

const developmentConfig: DataSourceOptions = {
  ...baseConfig,
  migrations: ["src/migrations/*.ts"],
  migrationsTableName: "typeorm_migrations",
};

const productionConfig: DataSourceOptions = {
  ...baseConfig,
  migrations: ["dist/migrations/*.js"],
  migrationsTableName: "typeorm_migrations",
};

const testConfig: DataSourceOptions = {
  ...baseConfig,
  database: `${config.database.database}_test`,
  migrations: ["src/migrations/*.ts"],
  migrationsTableName: "typeorm_migrations",
  dropSchema: true, // Clean slate for each test run
  synchronize: true, // Auto-create schema for tests
};

const getDataSourceConfig = (): DataSourceOptions => {
  switch (config.env) {
    case "production":
      return productionConfig;
    case "test":
      return testConfig;
    default:
      return developmentConfig;
  }
};

export const AppDataSource = new DataSource(getDataSourceConfig());

class Database {
  private static instance: Database;
  private _dataSource: DataSource | null = null;

  private constructor() {}

  public static getInstance(): Database {
    if (!Database.instance) {
      Database.instance = new Database();
    }
    return Database.instance;
  }

  public async connect(): Promise<DataSource> {
    if (this._dataSource?.isInitialized) {
      return this._dataSource;
    }

    try {
      this._dataSource = AppDataSource;
      await this._dataSource.initialize();

      logger.info("Database connected successfully", {
        environment: config.env,
        host: config.database.host,
        port: config.database.port,
        database: config.database.database,
      });

      return this._dataSource;
    } catch (error) {
      logger.error("Failed to connect to database", error);
      throw error;
    }
  }

  public get dataSource(): DataSource {
    if (!this._dataSource?.isInitialized) {
      throw new Error("Database not connected. Call connect() first.");
    }
    return this._dataSource;
  }

  public async disconnect(): Promise<void> {
    if (this._dataSource?.isInitialized) {
      await this._dataSource.destroy();
      this._dataSource = null;
      logger.info("Database disconnected");
    }
  }

  public async runMigrations(): Promise<void> {
    try {
      const migrations = await this.dataSource.runMigrations();
      if (migrations.length === 0) {
        logger.info("Database is already up to date");
      } else {
        logger.info(`Ran ${migrations.length} migrations`, {
          migrations: migrations.map((m) => m.name),
        });
      }
    } catch (error) {
      logger.error("Failed to run migrations", error);
      throw error;
    }
  }

  public async rollbackMigrations(): Promise<void> {
    try {
      await this.dataSource.undoLastMigration();
      logger.info("Rolled back last migration");
    } catch (error) {
      logger.error("Failed to rollback migrations", error);
      throw error;
    }
  }
}

export const database = Database.getInstance();
