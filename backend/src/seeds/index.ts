import "reflect-metadata";
import { database } from "@/config/database";
import { createLogger } from "@/utils/logger";
import { Interview, InterviewQuestion } from "@/entities";
import { DifficultyLevel, InterviewStatus, QuestionType } from "@/types";

const logger = createLogger("DatabaseSeeder");

async function seedDatabase() {
  try {
    await database.connect();

    const interviewRepository = database.dataSource.getRepository(Interview);
    const questionRepository =
      database.dataSource.getRepository(InterviewQuestion);

    // Clear existing data
    await questionRepository.delete({});
    await interviewRepository.delete({});

    // Create sample interview
    const interview = interviewRepository.create({
      title: "Excel Fundamentals Assessment",
      description:
        "Basic Excel skills assessment covering formulas, functions, and data manipulation",
      difficulty_level: DifficultyLevel.BEGINNER,
      estimated_duration: 30,
      status: InterviewStatus.ACTIVE,
    });

    const savedInterview = await interviewRepository.save(interview);

    // Create sample questions
    const questions = [
      {
        interview_id: savedInterview.id,
        question_text:
          "What is the formula to calculate the sum of cells A1 to A10?",
        question_type: QuestionType.FORMULA,
        expected_answer: "=SUM(A1:A10)",
        points: 5,
        order_index: 1,
        excel_scenario: {
          data_setup: "Column A contains numbers 1-10",
          required_formulas: ["SUM"],
          expected_output: "55",
          hints: ["Use the SUM function", "Specify the range A1:A10"],
        },
      },
      {
        interview_id: savedInterview.id,
        question_text: "How do you create an absolute reference in Excel?",
        question_type: QuestionType.MULTIPLE_CHOICE,
        expected_answer: "Use $ symbol before column and row references",
        points: 3,
        order_index: 2,
      },
      {
        interview_id: savedInterview.id,
        question_text:
          "Write a VLOOKUP formula to find a value in column C based on a lookup value in A1",
        question_type: QuestionType.FORMULA,
        expected_answer: "=VLOOKUP(A1,range,column_index,FALSE)",
        points: 8,
        order_index: 3,
        excel_scenario: {
          data_setup: "Table with lookup data in columns A-D",
          required_formulas: ["VLOOKUP"],
          expected_output: "Corresponding value from column C",
          hints: [
            "Use FALSE for exact match",
            "Specify the correct column index",
          ],
        },
      },
    ];

    const createdQuestions = questionRepository.create(questions);
    await questionRepository.save(createdQuestions);

    logger.info("Database seeded successfully", {
      interviewsCreated: 1,
      questionsCreated: questions.length,
    });

    await database.disconnect();
  } catch (error) {
    logger.error("Failed to seed database", error);
    process.exit(1);
  }
}

if (require.main === module) {
  seedDatabase().catch((error) => {
    console.error("Seeding failed:", error);
    process.exit(1);
  });
}

export { seedDatabase };
