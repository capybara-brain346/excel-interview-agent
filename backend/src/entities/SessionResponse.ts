import { Entity, Column, ManyToOne, JoinColumn, Index, Unique } from "typeorm";
import { BaseEntity } from "./BaseEntity";
import { InterviewSession } from "./InterviewSession";
import { InterviewQuestion } from "./InterviewQuestion";

@Entity("session_responses")
@Index(["session_id"])
@Index(["question_id"])
@Index(["is_correct"])
@Unique(["session_id", "question_id"])
export class SessionResponse extends BaseEntity {
  @Column({ type: "uuid" })
  session_id: string;

  @Column({ type: "uuid" })
  question_id: string;

  @Column({ type: "text" })
  answer: string;

  @Column({ type: "decimal", precision: 5, scale: 2, nullable: true })
  score?: number;

  @Column({ type: "integer", comment: "Time taken in seconds" })
  time_taken: number;

  @Column({ type: "boolean", default: false })
  is_correct: boolean;

  @ManyToOne(() => InterviewSession, (session) => session.responses, {
    onDelete: "CASCADE",
  })
  @JoinColumn({ name: "session_id" })
  session: InterviewSession;

  @ManyToOne(() => InterviewQuestion, (question) => question.responses, {
    onDelete: "CASCADE",
  })
  @JoinColumn({ name: "question_id" })
  question: InterviewQuestion;
}
