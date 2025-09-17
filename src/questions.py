from typing import Dict, List
from src.models import InterviewQuestion, QuestionMetadata


EXCEL_QUESTIONS: Dict[str, List[InterviewQuestion]] = {
    "basic": [
        InterviewQuestion(
            metadata=QuestionMetadata(
                question_id="basic_sum",
                difficulty="basic",
                topic="formulas",
                expected_concepts=["SUM function", "cell references"],
                expected_formula="=SUM(A1:A10)",
            ),
            question_text="How would you calculate the total of values in cells A1 through A10?",
            context="You have a column of numbers and need to find their sum.",
        ),
        InterviewQuestion(
            metadata=QuestionMetadata(
                question_id="basic_average",
                difficulty="basic",
                topic="formulas",
                expected_concepts=["AVERAGE function", "range selection"],
                expected_formula="=AVERAGE(B1:B20)",
            ),
            question_text="What formula would you use to find the average of a range of cells B1:B20?",
            context="You need to calculate the mean value of a dataset.",
        ),
        InterviewQuestion(
            metadata=QuestionMetadata(
                question_id="basic_count",
                difficulty="basic",
                topic="formulas",
                expected_concepts=["COUNT function", "COUNTA function"],
                expected_formula="=COUNT(C1:C15)",
            ),
            question_text="How would you count the number of cells containing numbers in range C1:C15?",
            context="You need to count only numeric values, ignoring text and empty cells.",
        ),
    ],
    "intermediate": [
        InterviewQuestion(
            metadata=QuestionMetadata(
                question_id="intermediate_vlookup",
                difficulty="intermediate",
                topic="formulas",
                expected_concepts=["VLOOKUP", "table lookup", "exact match"],
                expected_formula="=VLOOKUP(lookup_value, table_array, col_index, FALSE)",
            ),
            question_text="Explain how you would use VLOOKUP to find a product price from a pricing table.",
            context="You have a product table with columns: Product ID, Product Name, Price. You need to lookup prices by Product ID.",
        ),
        InterviewQuestion(
            metadata=QuestionMetadata(
                question_id="intermediate_pivot",
                difficulty="intermediate",
                topic="pivot_tables",
                expected_concepts=["pivot table", "data summarization", "grouping"],
            ),
            question_text="How would you create a pivot table to summarize sales data by region and month?",
            context="You have sales data with columns: Date, Region, Salesperson, Product, Revenue.",
        ),
        InterviewQuestion(
            metadata=QuestionMetadata(
                question_id="intermediate_conditional",
                difficulty="intermediate",
                topic="formulas",
                expected_concepts=[
                    "IF function",
                    "conditional logic",
                    "nested conditions",
                ],
                expected_formula="=IF(condition, value_if_true, value_if_false)",
            ),
            question_text="How would you create a formula that assigns letter grades based on numeric scores (A: 90+, B: 80-89, C: 70-79, F: <70)?",
            context="You have a column of test scores and need to assign corresponding letter grades.",
        ),
    ],
    "advanced": [
        InterviewQuestion(
            metadata=QuestionMetadata(
                question_id="advanced_index_match",
                difficulty="advanced",
                topic="formulas",
                expected_concepts=["INDEX", "MATCH", "two-way lookup"],
                expected_formula="=INDEX(return_range, MATCH(lookup_value, lookup_range, 0))",
            ),
            question_text="Explain how INDEX/MATCH can be more flexible than VLOOKUP, and provide an example.",
            context="You need to perform lookups where the return column is to the left of the lookup column.",
        ),
        InterviewQuestion(
            metadata=QuestionMetadata(
                question_id="advanced_array_formula",
                difficulty="advanced",
                topic="formulas",
                expected_concepts=["array formulas", "SUMPRODUCT", "dynamic arrays"],
            ),
            question_text="How would you calculate the sum of products where multiple criteria are met without using SUMIFS?",
            context="You have sales data and need to sum revenue where both region='North' and product='Laptop'.",
        ),
        InterviewQuestion(
            metadata=QuestionMetadata(
                question_id="advanced_data_cleaning",
                difficulty="advanced",
                topic="data_cleaning",
                expected_concepts=[
                    "text functions",
                    "data validation",
                    "remove duplicates",
                ],
            ),
            question_text="Describe your approach to cleaning a dataset with inconsistent text formatting, duplicates, and missing values.",
            context="You've received a customer database with various data quality issues that need to be resolved.",
        ),
    ],
}


SCENARIO_QUESTIONS: List[InterviewQuestion] = [
    InterviewQuestion(
        metadata=QuestionMetadata(
            question_id="scenario_sales_analysis",
            difficulty="intermediate",
            topic="scenarios",
            expected_concepts=[
                "pivot tables",
                "charts",
                "data analysis",
                "business insights",
            ],
        ),
        question_text="""You've been given a sales dataset with 10,000 rows containing: Date, Region, Salesperson, Product Category, Product, Units Sold, Unit Price, Total Revenue.

Your manager asks you to:
1. Identify the top 5 performing products by revenue
2. Compare regional performance over the last 12 months
3. Find which salesperson has the most consistent performance
4. Create a dashboard showing key metrics

Walk me through your Excel approach step by step.""",
        context="This is a real-world scenario testing your ability to analyze business data and create actionable insights.",
    )
]


REFLECTION_QUESTIONS: List[str] = [
    "What Excel concepts do you feel most confident about, and which areas would you like to improve?",
    "Describe a challenging Excel problem you've solved recently. What made it difficult?",
    "How do you typically approach learning new Excel features or functions?",
    "What would you say are your current Excel skill level strengths and weaknesses?",
]
