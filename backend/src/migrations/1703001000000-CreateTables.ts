import { MigrationInterface, QueryRunner } from "typeorm";

export class CreateTables1703001000000 implements MigrationInterface {
  name = "CreateTables1703001000000";

  public async up(queryRunner: QueryRunner): Promise<void> {
    // Enable UUID extension
    await queryRunner.query(`CREATE EXTENSION IF NOT EXISTS "uuid-ossp"`);

    // Create interviews table
    await queryRunner.query(`
      CREATE TABLE "interviews" (
        "id" uuid NOT NULL DEFAULT uuid_generate_v4(),
        "title" character varying(255) NOT NULL,
        "description" text,
        "difficulty_level" character varying NOT NULL,
        "estimated_duration" integer NOT NULL,
        "status" character varying NOT NULL DEFAULT 'draft',
        "created_at" TIMESTAMP NOT NULL DEFAULT now(),
        "updated_at" TIMESTAMP NOT NULL DEFAULT now(),
        CONSTRAINT "PK_interviews" PRIMARY KEY ("id")
      )
    `);

    // Create difficulty_level enum constraint
    await queryRunner.query(`
      ALTER TABLE "interviews" ADD CONSTRAINT "CHK_interviews_difficulty_level" 
      CHECK ("difficulty_level" IN ('beginner', 'intermediate', 'advanced', 'expert'))
    `);

    // Create status enum constraint
    await queryRunner.query(`
      ALTER TABLE "interviews" ADD CONSTRAINT "CHK_interviews_status" 
      CHECK ("status" IN ('draft', 'active', 'archived'))
    `);

    // Create interview_questions table
    await queryRunner.query(`
      CREATE TABLE "interview_questions" (
        "id" uuid NOT NULL DEFAULT uuid_generate_v4(),
        "interview_id" uuid NOT NULL,
        "question_text" text NOT NULL,
        "question_type" character varying NOT NULL,
        "expected_answer" text,
        "points" integer NOT NULL DEFAULT 1,
        "order_index" integer NOT NULL,
        "excel_scenario" jsonb,
        "created_at" TIMESTAMP NOT NULL DEFAULT now(),
        "updated_at" TIMESTAMP NOT NULL DEFAULT now(),
        CONSTRAINT "PK_interview_questions" PRIMARY KEY ("id"),
        CONSTRAINT "UQ_interview_questions_interview_id_order_index" UNIQUE ("interview_id", "order_index")
      )
    `);

    // Create question_type enum constraint
    await queryRunner.query(`
      ALTER TABLE "interview_questions" ADD CONSTRAINT "CHK_interview_questions_question_type" 
      CHECK ("question_type" IN ('multiple_choice', 'text_input', 'formula', 'practical'))
    `);

    // Create interview_sessions table
    await queryRunner.query(`
      CREATE TABLE "interview_sessions" (
        "id" uuid NOT NULL DEFAULT uuid_generate_v4(),
        "interview_id" uuid NOT NULL,
        "candidate_name" character varying(255) NOT NULL,
        "candidate_email" character varying(255) NOT NULL,
        "status" character varying NOT NULL DEFAULT 'pending',
        "started_at" TIMESTAMP,
        "completed_at" TIMESTAMP,
        "total_score" numeric(5,2),
        "created_at" TIMESTAMP NOT NULL DEFAULT now(),
        "updated_at" TIMESTAMP NOT NULL DEFAULT now(),
        CONSTRAINT "PK_interview_sessions" PRIMARY KEY ("id")
      )
    `);

    // Create session status enum constraint
    await queryRunner.query(`
      ALTER TABLE "interview_sessions" ADD CONSTRAINT "CHK_interview_sessions_status" 
      CHECK ("status" IN ('pending', 'in_progress', 'completed', 'abandoned'))
    `);

    // Create session_responses table
    await queryRunner.query(`
      CREATE TABLE "session_responses" (
        "id" uuid NOT NULL DEFAULT uuid_generate_v4(),
        "session_id" uuid NOT NULL,
        "question_id" uuid NOT NULL,
        "answer" text NOT NULL,
        "score" numeric(5,2),
        "time_taken" integer NOT NULL,
        "is_correct" boolean NOT NULL DEFAULT false,
        "created_at" TIMESTAMP NOT NULL DEFAULT now(),
        "updated_at" TIMESTAMP NOT NULL DEFAULT now(),
        CONSTRAINT "PK_session_responses" PRIMARY KEY ("id"),
        CONSTRAINT "UQ_session_responses_session_id_question_id" UNIQUE ("session_id", "question_id")
      )
    `);

    // Add foreign key constraints
    await queryRunner.query(`
      ALTER TABLE "interview_questions" ADD CONSTRAINT "FK_interview_questions_interview_id" 
      FOREIGN KEY ("interview_id") REFERENCES "interviews"("id") ON DELETE CASCADE ON UPDATE NO ACTION
    `);

    await queryRunner.query(`
      ALTER TABLE "interview_sessions" ADD CONSTRAINT "FK_interview_sessions_interview_id" 
      FOREIGN KEY ("interview_id") REFERENCES "interviews"("id") ON DELETE CASCADE ON UPDATE NO ACTION
    `);

    await queryRunner.query(`
      ALTER TABLE "session_responses" ADD CONSTRAINT "FK_session_responses_session_id" 
      FOREIGN KEY ("session_id") REFERENCES "interview_sessions"("id") ON DELETE CASCADE ON UPDATE NO ACTION
    `);

    await queryRunner.query(`
      ALTER TABLE "session_responses" ADD CONSTRAINT "FK_session_responses_question_id" 
      FOREIGN KEY ("question_id") REFERENCES "interview_questions"("id") ON DELETE CASCADE ON UPDATE NO ACTION
    `);

    // Create indexes
    await queryRunner.query(
      `CREATE INDEX "IDX_interviews_status" ON "interviews" ("status")`
    );
    await queryRunner.query(
      `CREATE INDEX "IDX_interviews_difficulty_level" ON "interviews" ("difficulty_level")`
    );
    await queryRunner.query(
      `CREATE INDEX "IDX_interviews_created_at" ON "interviews" ("created_at")`
    );

    await queryRunner.query(
      `CREATE INDEX "IDX_interview_questions_interview_id" ON "interview_questions" ("interview_id")`
    );
    await queryRunner.query(
      `CREATE INDEX "IDX_interview_questions_question_type" ON "interview_questions" ("question_type")`
    );
    await queryRunner.query(
      `CREATE INDEX "IDX_interview_questions_order_index" ON "interview_questions" ("order_index")`
    );

    await queryRunner.query(
      `CREATE INDEX "IDX_interview_sessions_interview_id" ON "interview_sessions" ("interview_id")`
    );
    await queryRunner.query(
      `CREATE INDEX "IDX_interview_sessions_status" ON "interview_sessions" ("status")`
    );
    await queryRunner.query(
      `CREATE INDEX "IDX_interview_sessions_candidate_email" ON "interview_sessions" ("candidate_email")`
    );
    await queryRunner.query(
      `CREATE INDEX "IDX_interview_sessions_created_at" ON "interview_sessions" ("created_at")`
    );

    await queryRunner.query(
      `CREATE INDEX "IDX_session_responses_session_id" ON "session_responses" ("session_id")`
    );
    await queryRunner.query(
      `CREATE INDEX "IDX_session_responses_question_id" ON "session_responses" ("question_id")`
    );
    await queryRunner.query(
      `CREATE INDEX "IDX_session_responses_is_correct" ON "session_responses" ("is_correct")`
    );
  }

  public async down(queryRunner: QueryRunner): Promise<void> {
    // Drop tables in reverse order (due to foreign key constraints)
    await queryRunner.query(`DROP TABLE "session_responses"`);
    await queryRunner.query(`DROP TABLE "interview_sessions"`);
    await queryRunner.query(`DROP TABLE "interview_questions"`);
    await queryRunner.query(`DROP TABLE "interviews"`);
  }
}
