from langchain_openai import ChatOpenAI
from datetime import datetime
import uuid

from factory import OPENAI_CLIENT
from services.orchestration.tools.mongo import mongo_tools
from services.logger_service import LoggerUtils, LogLevel

logger = LoggerUtils("ReviewAgent", LogLevel.DEBUG)


class ReviewAgent:
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
            if tool.name in ["save_feedback", "save_tip_sheet"]
        }

    def provide_feedback(self, answer_plan_id, plan_text):
        """Provide feedback on an analysis plan"""
        prompt = f"""
        Review the following analysis plan and provide constructive feedback:
        {plan_text}
        
        Consider:
        1. Comprehensiveness of the approach
        2. Potential gaps or blind spots
        3. Methodological rigor
        4. Additional perspectives or data sources to consider
        
        Format your feedback as specific, actionable suggestions.
        """

        response = self.llm.invoke(prompt)
        feedback_text = response.content

        try:
            # Save feedback to MongoDB using the tool
            feedback_id = str(uuid.uuid4())
            self.mongo_tools["save_feedback"].func(
                id=feedback_id,
                answer_plan_id=answer_plan_id,
                feedback_text=feedback_text,
            )
            logger.debug(f"Saved feedback to MongoDB with ID: {feedback_id}")
        except Exception as e:
            logger.error(f"Error saving feedback to MongoDB: {str(e)}")

        return feedback_text

    def generate_tip_sheet(self, parent_id, bullet_points, parent_type="analysis"):
        """Generate a final tip sheet from analysis results"""
        try:
            # Create a prompt for tip sheet generation
            points_text = (
                "\n".join(bullet_points)
                if isinstance(bullet_points, list)
                else str(bullet_points)
            )
            prompt = f"""
            Based on the following analysis points, create a concise and impactful tip sheet:
            {points_text}
            
            The tip sheet should:
            1. Highlight the most important findings
            2. Present information in a clear, actionable format
            3. Include relevant statistics and data points
            4. Be easily digestible for a general audience
            
            Format each point as a clear, actionable bullet point starting with "-".
            Focus on practical implications and actionable insights.
            """

            response = self.llm.invoke(prompt)

            # Process the response into clean bullet points
            raw_points = response.content.split("\n")
            final_bullet_points = []

            for point in raw_points:
                point = point.strip()
                if point and (point.startswith("-") or point.startswith("•")):
                    # Clean up the point
                    clean_point = point.lstrip("-•").strip()
                    if clean_point:
                        final_bullet_points.append(clean_point)

            # Ensure we have at least some bullet points
            if not final_bullet_points:
                logger.warning("No valid bullet points generated, using raw response")
                final_bullet_points = [p.strip() for p in raw_points if p.strip()]

            try:
                # Save tip sheet to MongoDB using the tool
                tip_sheet_id = str(uuid.uuid4())
                self.mongo_tools["save_tip_sheet"].func(
                    id=tip_sheet_id,
                    parent_id=parent_id,
                    parent_type=parent_type,
                    final_bullet_points=final_bullet_points,
                )
                logger.debug(f"Saved tip sheet to MongoDB with ID: {tip_sheet_id}")
            except Exception as e:
                logger.error(f"Error saving tip sheet to MongoDB: {str(e)}")

            logger.info(f"Generated tip sheet with {len(final_bullet_points)} points")
            return final_bullet_points

        except Exception as e:
            logger.error(f"Error in generate_tip_sheet: {str(e)}")
            default_points = [
                "Consider the broader economic implications of current events",
                "Focus on digital transformation opportunities",
                "Prepare for emerging challenges in the financial sector",
            ]
            try:
                # Save default tip sheet to MongoDB
                self.mongo_tools["save_tip_sheet"].func(
                    id=str(uuid.uuid4()),
                    parent_id=parent_id,
                    parent_type=parent_type,
                    final_bullet_points=default_points,
                )
            except Exception as save_error:
                logger.error(
                    f"Error saving default tip sheet to MongoDB: {str(save_error)}"
                )
            return default_points
