from services.logger_service import LoggerUtils, LogLevel
from factory import OPENAI_CLIENT
from langchain.agents import initialize_agent, AgentType
from langchain_openai import ChatOpenAI
from langchain.tools import Tool
from datetime import datetime
import uuid

from services.orchestration.tools.tools import news_tool, topic_news_tool
from services.orchestration.tools.mongo import (
    mongo_tools,
    get_pending_search_topics,
    update_search_topic_status,
)

logger = LoggerUtils("CollectionAgent", LogLevel.DEBUG)


class CollectionAgent:
    def __init__(self, model_name="gpt-4", temperature=0):
        self.llm = ChatOpenAI(
            model_name=model_name,
            temperature=temperature,
            openai_api_key=OPENAI_CLIENT.api_key,
        )
        # Combine news tools with relevant MongoDB tools
        self.tools = [news_tool, topic_news_tool] + [
            tool
            for tool in mongo_tools
            if tool.name
            in [
                "save_news",
                "save_generation_log",
                "save_questions",
                "update_topic_status",
            ]
        ]
        self.agent = initialize_agent(
            tools=self.tools,
            llm=self.llm,
            agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
        )

    def collect_data(self, topic: str = None):
        """
        Collect data from various sources and log the process

        Args:
            topic (str, optional): Specific topic to search for. If None, gets general news.
        """
        start_time = datetime.now()
        topic_id = None  # Initialize topic_id

        try:
            # If no topic is provided, check for pending topics
            if topic is None:
                pending_topics = get_pending_search_topics()
                if pending_topics:
                    # Take the first pending topic
                    topic_data = pending_topics[0]
                    topic = topic_data["topic"]
                    topic_id = topic_data["id"]
                    logger.info(f"Processing pending topic: {topic}")

            # Choose which tool to use based on whether a topic is provided
            if topic:
                articles = topic_news_tool.func(topic)
                logger.debug(f"Collected {len(articles)} articles about {topic}")
            else:
                articles = news_tool.func("")
                logger.debug(f"Collected {len(articles)} articles from various sources")

            for article in articles:
                logger.debug(
                    f"Article from {article.get('source', 'unknown')}: {article.get('headline', 'No headline')}"
                )

            # Generate unique ID for the collection process
            collection_id = str(uuid.uuid4())

            # Save each article to the news collection using the tool
            saved_articles = []
            for article in articles:
                if isinstance(article, dict):
                    try:
                        # Find the save_news tool
                        save_news_tool = next(
                            tool for tool in self.tools if tool.name == "save_news"
                        )
                        save_news_tool.func(
                            title=article.get("headline", "No headline"),
                            status="collected",
                            source_links=[article.get("url", "")],
                            notion_link=None,
                        )
                        saved_articles.append(article)
                        logger.debug(
                            f"Saved article from {article.get('source', 'unknown')}: {article.get('headline', 'No headline')}"
                        )
                    except Exception as e:
                        logger.error(f"Error saving article to MongoDB: {str(e)}")

            # Prepare output data
            output_data = {
                "output": saved_articles,
                "message": f"Collected {len(saved_articles)} articles about {topic if topic else 'various topics'} from {len(set(a.get('source', '') for a in saved_articles))} sources",
                "articles": saved_articles,
            }

            # Calculate time spent
            time_spent = (datetime.now() - start_time).total_seconds()

            try:
                # Find the save_generation_log tool
                save_log_tool = next(
                    tool for tool in self.tools if tool.name == "save_generation_log"
                )
                # Log the generation process using the tool
                save_log_tool.func(
                    parent_id=collection_id,
                    parent_type="news",
                    sources_analyzed=len(saved_articles),
                    sources_used=len(saved_articles),
                    source_titles=[
                        (
                            f"[{article.get('source', 'unknown')}] {article.get('headline', 'No headline')}"
                            if isinstance(article, dict)
                            else str(article)
                        )
                        for article in saved_articles
                    ],
                    source_links=[
                        article.get("url", "") if isinstance(article, dict) else ""
                        for article in saved_articles
                    ],
                    time_spent=time_spent,
                )
                logger.debug("Saved generation log to MongoDB")

                # Update topic status if processing a pending topic
                if topic and topic_id:
                    update_search_topic_status(topic_id, "completed")
                    logger.info(f"Updated topic status to completed: {topic}")

            except Exception as e:
                logger.error(f"Error saving generation log to MongoDB: {str(e)}")
                if topic and topic_id:
                    update_search_topic_status(topic_id, "failed")

            logger.info(f"Data collection completed. Collection ID: {collection_id}")
            return collection_id, output_data

        except Exception as e:
            logger.error(f"Error in collect_data: {str(e)}")
            if topic and topic_id:
                update_search_topic_status(topic_id, "failed")
            return str(uuid.uuid4()), {
                "output": [],
                "message": f"Error collecting data: {str(e)}",
                "articles": [],
            }

    def generate_questions(self, collection_id, collected_data):
        """Generate questions based on collected data"""
        start_time = datetime.now()

        print("llm question generation-------------> 1")

        try:
            # Extract articles and context
            articles = (
                collected_data.get("articles", [])
                if isinstance(collected_data, dict)
                else []
            )

            # Create context from articles
            context = ""
            if articles:
                context = (
                    "Based on the following news articles from various sources:\n\n"
                )
                for article in articles:
                    if isinstance(article, dict):
                        context += f"Source: {article.get('source', 'unknown')}\n"
                        context += f"Title: {article.get('headline', '')}\n"
                        context += f"Summary: {article.get('summary', '')}\n\n"
            else:
                context = "No specific articles available. Generating questions based on general trends."

            # Create a prompt for question generation
            prompt = f"""
            Analyze the following news articles from various African sources and generate 2 insightful questions about their potential implications 
            for digital banking, financial services, and economic trends.

            News Context:
            {context}

            Consider these aspects when generating questions:
            1. Economic Impact:
               - How might these events influence financial markets?
               - What economic trends could affect banking services?
               - How do these events impact different African regions differently?

            2. Digital Transformation:
               - What opportunities for digital innovation emerge from these situations?
               - How might these events drive digital adoption?
               - What are the regional differences in digital transformation?

            3. Risk and Adaptation:
               - What new challenges might financial institutions face?
               - How might banks need to adapt their services?
               - What are the regulatory implications across different regions?

            4. Social and Market Changes:
               - What changing consumer needs are highlighted?
               - How might these events affect financial behavior?
               - What cultural and regional factors need consideration?

            Generate questions that:
            - Connect current events to financial sector implications
            - Explore potential ripple effects on digital services
            - Consider both challenges and opportunities
            - Think about long-term impacts and transformations
            - Account for regional differences and local contexts
            """
            print("llm question generation-------------> start")
            # Use the LLM to generate questions
            response = self.llm.invoke(prompt)
            print("llm question generation-------------> llm process")
            raw_questions = [
                q.strip() for q in response.content.split("\n") if q.strip()
            ]

            print("llm question generation-------------> working")

            # Calculate time spent
            time_spent = (datetime.now() - start_time).total_seconds()

            # Find the save_questions tool
            save_questions_tool = next(
                tool for tool in self.tools if tool.name == "save_questions"
            )

            # Process and save each question
            processed_questions = []
            for question in raw_questions:
                # Skip empty questions or those that don't look like questions
                if not question or not any(
                    q in question.lower()
                    for q in ["?", "how", "what", "why", "when", "where", "which"]
                ):
                    continue

                # Clean up the question format
                clean_question = question.strip()
                if not clean_question.endswith("?"):
                    clean_question += "?"

                # Remove any numbering at the start
                clean_question = clean_question.lstrip("0123456789.- ")

                try:
                    # Save to MongoDB using the tool
                    question_id = str(uuid.uuid4())
                    save_questions_tool.func(
                        id=question_id,
                        parent_id=collection_id,
                        parent_type="data_collection",
                        question_text=clean_question,
                        time_spent=time_spent,
                    )
                    processed_questions.append(clean_question)
                    logger.debug(f"Saved question to MongoDB: {clean_question}")
                except Exception as e:
                    logger.error(f"Error saving question to MongoDB: {str(e)}")

            logger.info(f"Generated {len(processed_questions)} questions")
            return processed_questions

        except Exception as e:
            logger.error(f"Error in generate_questions: {str(e)}")
            default_questions = [
                "How might current market events across Africa impact the adoption of digital financial services?",
                "What opportunities for digital innovation emerge from recent developments in different African regions?",
                "How should financial institutions adapt their services to address emerging challenges across Africa?",
            ]
            return default_questions
