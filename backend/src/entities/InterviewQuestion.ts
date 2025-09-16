import {
  Entity,
  Column,
  ManyToOne,
  OneToMany,
  JoinColumn,
  Index,
  Unique,
} from "typeorm";
import { BaseEntity } from "./BaseEntity";
import { Interview } from "./Interview";
import { SessionResponse } from "./SessionResponse";
import { QuestionType, ExcelScenario } from "@/types";

@Entity("interview_questions")
@Index(["interview_id"])
@Index(["question_type"])
@Index(["order_index"])
@Unique(["interview_id", "order_index"])
export class InterviewQuestion extends BaseEntity {
  @Column({ type: "uuid" })
  interview_id: string;

  @Column({ type: "text" })
  question_text: string;

  @Column({
    type: "enum",
    enum: QuestionType,
  })
  question_type: QuestionType;

  @Column({ type: "text", nullable: true })
  expected_answer?: string;

  @Column({ type: "integer", default: 1 })
  points: number;

  @Column({ type: "integer" })
  order_index: number;

  @Column({ type: "jsonb", nullable: true })
  excel_scenario?: ExcelScenario;

  @ManyToOne(() => Interview, (interview) => interview.questions, {
    onDelete: "CASCADE",
  })
  @JoinColumn({ name: "interview_id" })
  interview: Interview;

  @OneToMany(() => SessionResponse, (response) => response.question)
  responses: SessionResponse[];
}
