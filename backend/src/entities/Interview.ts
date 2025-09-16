import { Entity, Column, OneToMany, Index } from "typeorm";
import { BaseEntity } from "./BaseEntity";
import { InterviewQuestion } from "./InterviewQuestion";
import { InterviewSession } from "./InterviewSession";
import { DifficultyLevel, InterviewStatus } from "@/types";

@Entity("interviews")
@Index(["status"])
@Index(["difficulty_level"])
@Index(["created_at"])
export class Interview extends BaseEntity {
  @Column({ type: "varchar", length: 255 })
  title: string;

  @Column({ type: "text", nullable: true })
  description?: string;

  @Column({
    type: "enum",
    enum: DifficultyLevel,
  })
  difficulty_level: DifficultyLevel;

  @Column({ type: "integer", comment: "Duration in minutes" })
  estimated_duration: number;

  @Column({
    type: "enum",
    enum: InterviewStatus,
    default: InterviewStatus.DRAFT,
  })
  status: InterviewStatus;

  @OneToMany(() => InterviewQuestion, (question) => question.interview, {
    cascade: true,
    eager: false,
  })
  questions: InterviewQuestion[];

  @OneToMany(() => InterviewSession, (session) => session.interview)
  sessions: InterviewSession[];
}
