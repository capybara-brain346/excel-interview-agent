import {
  Entity,
  Column,
  ManyToOne,
  OneToMany,
  JoinColumn,
  Index,
} from "typeorm";
import { BaseEntity } from "./BaseEntity";
import { Interview } from "./Interview";
import { SessionResponse } from "./SessionResponse";
import { SessionStatus } from "@/types";

@Entity("interview_sessions")
@Index(["interview_id"])
@Index(["status"])
@Index(["candidate_email"])
@Index(["created_at"])
export class InterviewSession extends BaseEntity {
  @Column({ type: "uuid" })
  interview_id: string;

  @Column({ type: "varchar", length: 255 })
  candidate_name: string;

  @Column({ type: "varchar", length: 255 })
  candidate_email: string;

  @Column({
    type: "enum",
    enum: SessionStatus,
    default: SessionStatus.PENDING,
  })
  status: SessionStatus;

  @Column({ type: "timestamp", nullable: true })
  started_at?: Date;

  @Column({ type: "timestamp", nullable: true })
  completed_at?: Date;

  @Column({ type: "decimal", precision: 5, scale: 2, nullable: true })
  total_score?: number;

  @ManyToOne(() => Interview, (interview) => interview.sessions, {
    onDelete: "CASCADE",
  })
  @JoinColumn({ name: "interview_id" })
  interview: Interview;

  @OneToMany(() => SessionResponse, (response) => response.session, {
    cascade: true,
    eager: false,
  })
  responses: SessionResponse[];
}
