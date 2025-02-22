from services.logger_service import LoggerUtils, LogLevel
from services.agent_service.collection_agent import CollectionAgent
from services.agent_service.analysis_agent import AnalysisAgent
from services.agent_service.review_agent import ReviewAgent

from services.routes_service.keyword_service import convert_tip_to_french
from services.routes_service.keyword_service import analyze_style, blog_generated
from services.orchestration.tools.quality_metrics import blog_quality_metrics
from services.orchestration.tools.mongo import mongo_tools
from langchain_core.messages import AIMessage
import re
import time
from datetime import datetime
from bson.objectid import ObjectId

logger = LoggerUtils("AnalysisWorkflow", LogLevel.DEBUG)


def format_time(seconds):
    """Format seconds into a readable time string"""
    minutes = int(seconds // 60)
    remaining_seconds = int(seconds % 60)
    return f"{minutes:02d}:{remaining_seconds:02d}"


def run_analysis_workflow(topic: str = None):
    """
    Run the complete analysis workflow for a given topic.
    Returns the collection_id of the saved blog.

    Args:
        topic (str, optional): Specific topic to analyze. If None, analyzes general news.

    Returns:
        str: The collection_id of the saved blog.
    """
    try:
        print("\n=== Starting Digital Banking Analysis Workflow ===\n")
        if topic:
            print(f"Analyzing topic: {topic}")
            logger.info(f"Starting analysis workflow for topic: {topic}")

        # Initialize agents
        collection_agent = CollectionAgent()
        analysis_agent = AnalysisAgent()
        review_agent = ReviewAgent()

        # Step 1: Data Collection
        print("Step 1: Collecting Data...")
        start_time = time.time()
        collection_id, collected_data = collection_agent.collect_data(topic)
        if not collection_id:
            raise Exception("Failed to generate collection ID during data collection")
        collection_time = time.time() - start_time
        print(f"✓ Data collection completed in {format_time(collection_time)}")
        print(f"Collection ID: {collection_id}")
        logger.info(f"Data collection completed. Collection ID: {collection_id}")

        # Step 2: Question Generation
        print("\nStep 2: Generating Questions...")
        start_time = time.time()
        questions = collection_agent.generate_questions(collection_id, collected_data)
        question_time = time.time() - start_time
        print(f"✓ Generated {len(questions)} questions in {format_time(question_time)}")

        # Save questions to MongoDB
        save_questions_tool = next(
            (tool for tool in mongo_tools if tool.name == "save_questions"), None
        )
        if not save_questions_tool:
            logger.error("Could not find save_questions tool")
            raise Exception("Failed to find save_questions tool")

        # Process all questions
        print("\nStep 3: Analysis and Review Process...\n")
        all_bullet_points = []

        for i, question in enumerate(questions, 1):
            # Generate a unique question ID using ObjectId
            question_id = str(ObjectId())
            logger.debug(f"Processing question {i} with ID: {question_id}")

            try:
                # Validate question text
                if not question or not isinstance(question, str):
                    logger.error(
                        f"Invalid question format for question {i}: {question}"
                    )
                    continue

                # Save question to MongoDB
                logger.debug(
                    f"Attempting to save question to MongoDB: {question[:100]}..."
                )
                save_questions_tool.func(
                    id=question_id,
                    parent_id=collection_id,
                    parent_type="data_collection",
                    question_text=question,
                    time_spent=question_time / len(questions),
                )
                logger.debug(
                    f"Successfully saved question {i} to MongoDB with ID: {question_id}"
                )

                print(f"Analyzing Question {i}: {question}")

                # Create initial analysis plan
                print(f"  Creating initial analysis plan for Question {i}...")
                plan_id, plan_text = analysis_agent.create_answer_plan(
                    question_id=question_id, question=question
                )
                print(f"  ✓ Plan created (ID: {plan_id})")

                # Get feedback on the plan
                print(f"  Getting editorial feedback for Question {i}...")
                feedback = review_agent.provide_feedback(plan_id, plan_text)
                print("  ✓ Feedback received")
                print(f"  Feedback summary: {feedback[:100]}...")

                # Create revised plan based on feedback
                print(f"  Creating revised analysis plan for Question {i}...")
                revised_plan_id, revised_plan_text = analysis_agent.create_answer_plan(
                    question_id=question_id, question=question, version=2
                )
                print(f"  ✓ Revised plan created (ID: {revised_plan_id})")

                # Execute analysis
                print(f"  Executing analysis for Question {i}...")
                bullet_points = analysis_agent.execute_analysis(
                    question_id=question_id,
                    question=question,
                    plan_text=revised_plan_text,
                )
                print(f"  ✓ Analysis completed for Question {i}")
                print("  Key findings:")
                for point in bullet_points[:3]:
                    print(f"    • {point}")

                # Add to collection of all bullet points with clear separation
                all_bullet_points.extend(
                    [
                        f"\nQuestion {i}: {question}",
                        "Findings:",
                        *bullet_points,
                        "\n",  # Add extra spacing between questions
                    ]
                )
                print(f"\n✓ Completed analysis for Question {i}\n")

            except Exception as e:
                logger.error(f"Error processing question {i}: {str(e)}")
                logger.error(f"Question text: {question}")
                logger.error(f"Question ID: {question_id}")
                # Continue with next question instead of failing completely
                continue

        # Generate final tip sheet from all findings
        print("\nGenerating final tip sheet...")
        final_tips = review_agent.generate_tip_sheet(
            parent_id=collection_id,
            bullet_points=all_bullet_points,
            parent_type="insights",
        )
        print("✓ Final tip sheet generated\n")

        # Display recommendations
        print("Key recommendations:")
        for tip in final_tips:
            print(f"  • {tip}")

        # Generate French tips
        print("################ Generating Blog ######################")
        try:
            logger.debug(
                f"Starting French blog generation process for collection_id: {collection_id}"
            )
            # Convert final tips to French
            logger.debug(f"Converting tips to French. Tips count: {len(final_tips)}")
            french_tips = convert_tip_to_french(final_tips, collection_id)
            logger.debug(
                f"French tips generated successfully. Length: {len(french_tips)}"
            )
            logger.debug(f"French tips preview: {french_tips[:200]}...")

            # Analyze the French tips to get style metrics
            logger.debug("Analyzing style metrics for French tips")
            style_metrics = analyze_style(french_tips)
            logger.debug(f"Style metrics calculated: {style_metrics}")

            # Create template variables with required parameters
            template_vars = {
                "topic": topic if topic else "actualités générales",
                "formality_score": 0.8,  # High formality
                "complex_words_ratio": style_metrics.get("complex_words_ratio", 0.3),
                "similes": style_metrics.get(
                    "similes", 3
                ),  # Number of similes to include
                "tone": "professional",
            }
            logger.debug(f"Template variables prepared: {template_vars}")

            # Generate the blog using the French tips
            logger.debug("Generating blog content from French tips")
            blog_generation = blog_generated(french_tips, template_vars)
            if hasattr(blog_generation, "content"):
                content = blog_generation.content
                logger.debug(
                    f"Blog content generated successfully. Length: {len(content)}"
                )
                logger.debug("Content preview: " + content[:200] + "...")

                # Generate blog title
                blog_title = (
                    f"Analyse: {topic if topic else 'Actualités bancaires numériques'}"
                )

                # Save the French blog to MongoDB
                save_french_blog_tool = next(
                    (tool for tool in mongo_tools if tool.name == "save_french_blog"),
                    None,
                )
                if save_french_blog_tool:
                    logger.debug(
                        f"Found save_french_blog tool. Attempting to save blog with collection_id: {collection_id}"
                    )
                    try:
                        saved_blog_id = save_french_blog_tool.func(
                            collection_id=collection_id,
                            blog_content=content,
                            blog_title=blog_title,
                            blog_published_date=datetime.now(),
                        )
                        if saved_blog_id:
                            logger.debug(
                                f"French blog saved successfully with ID: {saved_blog_id}"
                            )
                        else:
                            logger.error("Failed to save French blog: No ID returned")
                            raise Exception(
                                "Failed to save French blog: No ID returned"
                            )
                    except Exception as e:
                        logger.error(f"Error saving French blog: {str(e)}")
                        raise Exception(f"Failed to save French blog: {str(e)}")
                else:
                    logger.error("save_french_blog tool not found in mongo_tools")
                    raise Exception("Failed to save French blog: tool not found")

                # Calculate and save quality metrics
                logger.debug("Calculating quality metrics for the blog")
                blog_quality_metrics(content, collection_id)
                logger.debug("Quality metrics calculated and saved")
                logger.info(
                    f"Analysis workflow completed successfully. Collection ID: {collection_id}"
                )

                return collection_id  # Return the collection_id for tracking
            else:
                logger.error("Blog generation response does not contain content")
                logger.error(f"Blog generation object: {blog_generation}")
                raise Exception("Blog generation failed: No content in response")
        except Exception as e:
            logger.error(f"Error in French blog generation process: {str(e)}")
            logger.error(
                "Style metrics:",
                style_metrics if "style_metrics" in locals() else "Not available",
            )
            raise
    except Exception as e:
        logger.error(f"Error in analysis workflow: {str(e)}")
        logger.error(
            "Style metrics:",
            style_metrics if "style_metrics" in locals() else "Not available",
        )
        raise  # Re-raise the exception to ensure it's properly handled


if __name__ == "__main__":
    try:
        # You can specify a topic here
        topic = "digital banking in Africa"  # or None for general news
        collection_id = run_analysis_workflow(topic)
        print(
            f"\nAll results have been saved to MongoDB with collection ID: {collection_id}"
        )
    except Exception as e:
        logger.error(f"Error during analysis: {str(e)}")
        print(f"\nError during analysis: {str(e)}")
