from services.logger_service import LoggerUtils, LogLevel
from factory import OPENAI_CLIENT
from langchain_openai import ChatOpenAI
from datetime import datetime
import uuid

from services.orchestration.tools.mongo import mongo_tools

logger = LoggerUtils("AnalysisAgent", LogLevel.DEBUG)


class AnalysisAgent:
    def __init__(self, model_name="gpt-4", temperature=0):
        self.llm = ChatOpenAI(
            model_name=model_name,
            temperature=temperature,
            openai_api_key=OPENAI_CLIENT.api_key,
        )
        # Get relevant MongoDB tools
        self.mongo_tools = {
            tool.name: tool
            for tool in mongo_tools
            if tool.name in ["save_answer_plan", "save_final_result"]
        }

    def create_answer_plan(self, question_id, question, version=1):
        """Create an answer plan for a given question"""
        prompt = f"""
        Create a detailed analysis plan to answer the following question:
        {question}
        
        The plan should:
        1. Outline specific data sources to analyze
        2. Define key metrics and indicators to examine
        3. Specify analytical approaches and methodologies
        4. Consider potential challenges and limitations
        """

        print("llm-------------> start")
        response = self.llm.invoke(prompt)
        plan_text = response.content
        print("llm-------------> working")

        try:
            # Save the answer plan to MongoDB using the tool
            plan_id = str(uuid.uuid4())
            self.mongo_tools["save_answer_plan"].func(
                id=plan_id,
                question_id=question_id,
                version=version,
                plan_text=plan_text,
            )
            logger.debug(f"Saved answer plan to MongoDB with ID: {plan_id}")
        except Exception as e:
            logger.error(f"Error saving answer plan to MongoDB: {str(e)}")

        return plan_id, plan_text

    def execute_analysis(self, question_id, question, plan_text):
        """Execute the analysis based on the approved plan"""
        try:
            prompt = f"""
            Based on the following analysis plan:
            {plan_text}
            
            Provide a detailed answer to the question:
            {question}
            
            Format your response as a list of key findings and insights.
            Each point should:
            - Start with a bullet point (-)
            - Be supported by data and evidence where possible
            - Be clear and actionable
            - Provide specific insights or recommendations
            
            Make sure each point is on a new line and starts with a dash (-).
            """

            response = self.llm.invoke(prompt)

            # Process the response into clean bullet points
            raw_points = response.content.split("\n")
            bullet_points = []

            for point in raw_points:
                point = point.strip()
                if point and (point.startswith("-") or point.startswith("•")):
                    # Clean up the point
                    clean_point = point.lstrip("-•").strip()
                    if clean_point:
                        bullet_points.append(clean_point)

            # If no bullet points were found, try to create them from the raw text
            if not bullet_points:
                logger.warning(
                    "No bullet points found in response, processing raw text"
                )
                bullet_points = [p.strip() for p in raw_points if p.strip()]

            # Ensure we have at least some content
            if not bullet_points:
                bullet_points = [
                    "No specific insights could be generated from the analysis"
                ]

            logger.debug(f"Generated bullet points: {bullet_points}")

            try:
                # Save the final results to MongoDB using the tool
                result_id = str(uuid.uuid4())
                self.mongo_tools["save_final_result"].func(
                    id=result_id, question_id=question_id, bullet_points=bullet_points
                )
                logger.debug(f"Saved final results to MongoDB with ID: {result_id}")
            except Exception as e:
                logger.error(f"Error saving final results to MongoDB: {str(e)}")

            return bullet_points

        except Exception as e:
            logger.error(f"Error in execute_analysis: {str(e)}")
            default_points = [
                "Analysis could not be completed due to an error",
                "Please review the analysis plan and try again",
            ]
            try:
                # Still save to MongoDB even in case of error
                self.mongo_tools["save_final_result"].func(
                    id=str(uuid.uuid4()),
                    question_id=question_id,
                    bullet_points=default_points,
                )
            except Exception as save_error:
                logger.error(
                    f"Error saving default results to MongoDB: {str(save_error)}"
                )
            return default_points
