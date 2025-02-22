from pymongo import MongoClient
from datetime import datetime
from bson.objectid import ObjectId
from langchain.agents import Tool

# MongoDB connection setup
client = MongoClient("mongodb://localhost:27017")  # Local MongoDB connection
db = client["ericDb"]  # Database name

# Collections (Representing Tables)
users_collection = db["users"]
news_collection = db["news"]
quality_metrics_collection = db["quality_metrics"]
generation_logs_collection = db["generation_logs"]
tip_sheets_collection = db["tip_sheets"]
questions_collection = db["questions"]
answer_plans_collection = db["answer_plans"]
feedback_collection = db["feedback"]
final_results_collection = db["final_results"]
nominations_collection = db["nominations"]
insights_collection = db["insights"]
insight_keywords_collection = db["insight_keywords"]
insight_metadata_collection = db["insight_metadata"]
topics_collection = db["topics"]
settings_collection = db["settings"]
articles_collection = db["articles"]
trusted_sources_collection = db["trusted_sources"]
area_preferences_collection = db["area_preferences"]
api_keys_collection = db["api_keys"]

french_tips_collection = db["french_tips"]

# Add new collection for search topics
search_topics_collection = db["search_topics"]

# Add new collection for French blogs
french_blogs_collection = db["french_blogs"]


def save_french_tips_to_mongodb(parent_id, french_tips):
    """
    Saves feedback related to an answer plan in the MongoDB database.

    Parameters:
        id (str): The ID of the related answer plan.
        french_tips (str): The french tips

    Returns:
        None
    """
    french_tip_data = {
        "parent_id": parent_id,
        "french_tips": french_tips,
        "created_at": datetime.now(),
    }

    result = french_tips_collection.insert_one(french_tip_data)
    print(f"French tips saved successfully with ID: {result.inserted_id}")


# Function to insert a user into the users collection
def save_user_to_mongodb(username, email, password, otp=None):
    """
    Saves a user to the MongoDB database.

    Parameters:
        username (str): The username of the user.
        email (str): The email address of the user.
        password (str): The hashed password of the user.
        otp (str, optional): The one-time password for authentication. Default is None.

    Returns:
        None
    """
    user_data = {
        "username": username,
        "email": email,
        "password": password,  # Store hashed password
        "otp": otp,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }

    result = users_collection.insert_one(user_data)
    print(f"User '{username}' saved successfully with ID: {result.inserted_id}")


def save_news_to_mongodb(title, status, source_links=None, notion_link=None):
    """
    Saves a news item to the MongoDB database.

    Parameters:
        title (str): The title of the news item.
        status (str): The current status of the news (e.g., 'pending', 'verified').
        source_links (list, optional): A list of source links for the news. Default is None.
        notion_link (str, optional): A Notion link associated with the news item. Default is None.

    Returns:
        None
    """
    news_data = {
        "title": title,
        "generated_on": datetime.now(),
        "status": status,
        "source_links": source_links,
        "notion_link": notion_link,
        "updated_at": datetime.now(),
    }

    result = news_collection.insert_one(news_data)
    print(f"News item '{title}' saved successfully with ID: {result.inserted_id}")


def save_quality_metrics_to_mongodb(
    parent_id,
    parent_type,
    human_writing_score,
    plagiarism_score,
    fact_verification,
    trusted_source_score,
):
    """
    Saves quality metrics for a news item or user-generated content to the MongoDB database.

    Parameters:
        parent_id (str): The ID of the parent document (news item or user-generated content).
        parent_type (str): The type of the parent document (e.g., 'news', 'user_content').
        human_writing_score (float): Score indicating human-like writing quality.
        plagiarism_score (float): Score indicating plagiarism percentage (lower is better).
        fact_verification (float): Score indicating the accuracy of facts (higher is better).
        trusted_source_score (float): Score indicating reliability of sources (higher is better).

    Returns:
        None
    """
    metrics_data = {
        "parent_id": parent_id,
        "parent_type": parent_type,
        "human_writing_score": human_writing_score,
        "plagiarism_score": plagiarism_score,
        "fact_verification": fact_verification,
        "trusted_source_score": trusted_source_score,
        "created_at": datetime.now(),
    }

    result = quality_metrics_collection.insert_one(metrics_data)
    print(f"Quality metrics saved with ID: {result.inserted_id}")


# Function to insert a generation log
def save_generation_log_to_mongodb(
    parent_id,
    parent_type,
    sources_analyzed,
    sources_used,
    source_titles,
    source_links,
    time_spent,
):
    """
    Saves a generation log entry to the MongoDB database.

    Parameters:
        parent_id (str): The ID of the parent document (e.g., news item, insight).
        parent_type (str): The type of the parent document.
        sources_analyzed (int): The number of sources analyzed for the generation.
        sources_used (int): The number of sources actually used.
        source_titles (list): A list of titles of the sources used.
        source_links (list): A list of links to the sources used.
        time_spent (float): The time spent on the generation process in seconds.

    Returns:
        None
    """
    generation_log_data = {
        "parent_id": parent_id,
        "parent_type": parent_type,
        "sources_analyzed": sources_analyzed,
        "sources_used": sources_used,
        "source_titles": source_titles,
        "source_links": source_links,
        "time_spent": time_spent,
        "created_at": datetime.now(),
    }

    result = generation_logs_collection.insert_one(generation_log_data)
    print(f"Generation log saved with ID: {result.inserted_id}")


def save_tip_sheet_to_mongodb(id, parent_id, parent_type, final_bullet_points):
    """
    Saves a tip sheet to the MongoDB database.

    Parameters:
        id (str): The unique identifier for the tip sheet.
        parent_id (str): The ID of the parent document (e.g., news, nomination).
        parent_type (str): The type of the parent document. Must be one of: 'news', 'nominations', 'insights', 'topics'.
        final_bullet_points (list): A list of final bullet points in the tip sheet.

    Returns:
        None
    """
    if parent_type not in ["news", "nominations", "insights", "topics"]:
        print(
            "Invalid parent_type. Must be one of: 'news', 'nominations', 'insights', 'topics'."
        )
        return

    tip_sheet_data = {
        "id": id,
        "parent_id": parent_id,
        "parent_type": parent_type,
        "final_bullet_points": final_bullet_points,
        "created_at": datetime.now(),
    }

    result = tip_sheets_collection.insert_one(tip_sheet_data)
    print(f"Tip sheet saved with ID: {result.inserted_id}")


def save_questions_to_mongo(id, parent_id, parent_type, question_text, time_spent=None):
    """
    Saves a question entry to the MongoDB database.

    Parameters:
        id (str): The unique identifier for the question.
        parent_id (str): The ID of the parent document (e.g., news, topic).
        parent_type (str): The type of the parent document. Must be one of: 'news', 'nominations', 'insights', 'topics', 'data_collection'.
        question_text (str): The text of the question.
        time_spent (float, optional): The time spent formulating the question. Default is None.

    Returns:
        None
    """
    if parent_type not in [
        "news",
        "nominations",
        "insights",
        "topics",
        "data_collection",
    ]:
        print(
            "Invalid parent_type. Must be one of: 'news', 'nominations', 'insights', 'topics', 'data_collection'."
        )
        return

    question_data = {
        "id": id,
        "parent_id": parent_id,
        "parent_type": parent_type,
        "question_text": question_text,
        "time_spent": time_spent if time_spent else None,
        "created_at": datetime.now(),
        "agent_info": {
            "name": "Collection Agent",
            "type": "GPT-4",
            "role": "Question Generation",
        },
    }

    result = questions_collection.insert_one(question_data)
    print(f"Question saved successfully with ID: {result.inserted_id}")


# Function to insert an answer plan
def save_answer_plan_to_mongodb(id, question_id, version, plan_text):
    """
    Saves an answer plan to the MongoDB database.

    Parameters:
        id (str): The unique identifier for the answer plan.
        question_id (str): The ID of the related question.
        version (int): The version number of the answer plan.
        plan_text (str): The text content of the answer plan.

    Returns:
        None
    """
    answer_plan_data = {
        "id": id,
        "question_id": question_id,
        "version": version,
        "plan_text": plan_text,
        "created_at": datetime.now(),
        "agent_info": {
            "name": "Analysis Agent",
            "type": "GPT-4",
            "role": "Plan Creation",
        },
    }

    result = answer_plans_collection.insert_one(answer_plan_data)
    print(f"Answer plan saved successfully with ID: {result.inserted_id}")


def save_feedback_to_mongodb(id, answer_plan_id, feedback_text):
    """
    Saves feedback related to an answer plan in the MongoDB database.

    Parameters:
        id (str): The unique identifier for the feedback.
        answer_plan_id (str): The ID of the related answer plan.
        feedback_text (str): The feedback text provided.

    Returns:
        None
    """
    feedback_data = {
        "id": id,
        "answer_plan_id": answer_plan_id,
        "feedback_text": feedback_text,
        "created_at": datetime.now(),
        "agent_info": {
            "name": "Review Agent",
            "type": "GPT-4",
            "role": "Plan Review and Feedback",
        },
    }

    result = feedback_collection.insert_one(feedback_data)
    print(f"Feedback saved successfully with ID: {result.inserted_id}")


def save_final_result_to_mongodb(id, question_id, bullet_points):
    """
    Saves the final result for a question in the MongoDB database.

    Parameters:
        id (str): The unique identifier for the final result.
        question_id (str): The ID of the related question.
        bullet_points (list): A list of bullet points summarizing the final result.

    Returns:
        None
    """
    final_result_data = {
        "id": id,
        "question_id": question_id,
        "bullet_points": bullet_points,
        "created_at": datetime.now(),
        "agent_info": {
            "name": "Analysis Agent",
            "type": "GPT-4",
            "role": "Analysis Execution",
        },
    }

    result = final_results_collection.insert_one(final_result_data)
    print(f"Final result saved successfully with ID: {result.inserted_id}")


# Function to insert a nomination
def save_nomination_to_mongodb(id, title, sources_link, appointee, status):
    """
    Saves a nomination entry to the MongoDB database.

    Parameters:
        id (str): The unique identifier for the nomination.
        title (str): The title of the nomination.
        sources_link (list): A list of links to the sources related to the nomination.
        appointee (str): The name of the appointee.
        status (str): The current status of the nomination. Must be one of:
                      'Generated', 'Published', 'In Progress', 'Failed'.

    Returns:
        response = requests.get(url, headers=headers, timeout=10)

        if resp
        None
    """
    if status not in ["Generated", "Published", "In Progress", "Failed"]:
        print(
            "Invalid status. Must be one of: 'Generated', 'Published', 'In Progress', 'Failed'."
        )
        return

    nomination_data = {
        "id": id,
        "title": title,
        "sources_link": sources_link if sources_link else None,
        "appointee": appointee,
        "generated_on": datetime.now(),
        "status": status,
    }

    result = nominations_collection.insert_one(nomination_data)
    print(f"Nomination '{title}' saved successfully with ID: {result.inserted_id}")


def save_insight_to_mongodb(
    id,
    title,
    scheduled_on,
    source_links,
    possible_back_links=None,
    notion_link=None,
    status="Generated",
):
    """
    Saves an insight entry to the MongoDB database.

    Parameters:
        title (str): The title of the insight.
        scheduled_on (str, optional): The date the insight is scheduled to be released. Default is None.
        source_links (list): A list of links to the sources related to the insight.
        possible_back_links (list, optional): A list of potential back links for the insight. Default is None.
        notion_link (str, optional): A Notion link related to the insight. Default is None.
        status (str, optional): The current status of the insight. Must be one of:
                                 'Generated', 'Published', 'In Progress', 'Failed'. Default is 'Generated'.

    Returns:
        None
    """
    if status not in ["Generated", "Published", "In Progress", "Failed"]:
        print(
            "Invalid status. Must be one of: 'Generated', 'Published', 'In Progress', 'Failed'."
        )
        return

    insight_data = {
        "title": title,
        "scheduled_on": scheduled_on if scheduled_on else None,
        "generated_on": datetime.now(),
        "status": status,
        "source_links": source_links,
        "possible_back_links": possible_back_links if possible_back_links else None,
        "notion_link": notion_link if notion_link else None,
        "updated_at": datetime.now(),
    }

    result = insights_collection.insert_one(insight_data)
    print(f"Insight '{title}' saved successfully with ID: {result.inserted_id}")


def save_insight_keyword_to_mongodb(id, insight_id, keyword, keyword_type):
    """
    Saves a keyword related to an insight to the MongoDB database.

    Parameters:
        id (str): The unique identifier for the insight keyword.
        insight_id (str): The ID of the related insight.
        keyword (str): The keyword associated with the insight.
        keyword_type (str): The type of the keyword. Must be one of:
                            'Manual' or 'AI-Generated'.

    Returns:
        None
    """
    if keyword_type not in ["Manual", "AI-Generated"]:
        print("Invalid keyword_type. Must be one of: 'Manual', 'AI-Generated'.")
        return

    insight_keyword_data = {
        "id": id,
        "insight_id": insight_id,
        "keyword": keyword,
        "keyword_type": keyword_type,
        "created_at": datetime.now(),
    }

    result = insight_keywords_collection.insert_one(insight_keyword_data)
    print(
        f"Insight keyword '{keyword}' saved successfully with ID: {result.inserted_id}"
    )


# Function to insert insight metadata
def save_insight_metadata_to_mongodb(
    id, insight_id, used_keywords=None, possible_back_links=None
):
    """
    Saves metadata related to an insight to the MongoDB database.

    Parameters:
        id (str): The unique identifier for the insight metadata.
        insight_id (str): The ID of the related insight.
        used_keywords (list, optional): A list of keywords used in the insight. Default is None.
        possible_back_links (list, optional): A list of possible backlinks related to the insight. Default is None.

    Returns:
        None
    """
    insight_metadata_data = {
        "id": id,
        "insight_id": insight_id,
        "used_keywords": used_keywords if used_keywords else None,
        "possible_back_links": possible_back_links if possible_back_links else None,
        "created_at": datetime.now(),
    }

    result = insight_metadata_collection.insert_one(insight_metadata_data)
    print(f"Insight metadata saved successfully with ID: {result.inserted_id}")


def save_topic_to_mongodb(
    id,
    title,
    status,
    created_by,
    scheduled_on=None,
    possible_back_links=None,
    notion_link=None,
    source_links=None,
):
    """
    Saves a topic entry to the MongoDB database.

    Parameters:
        id (str): The unique identifier for the topic.
        title (str): The title of the topic.
        status (str): The current status of the topic. Must be one of: 'Generated', 'Published', 'In Progress', 'Failed'.
        created_by (str): The user who created the topic.
        scheduled_on (str, optional): The date the topic is scheduled to be released. Default is None.
        possible_back_links (list, optional): A list of potential back links for the topic. Default is None.
        notion_link (str, optional): A Notion link related to the topic. Default is None.
        source_links (list, optional): A list of links to the sources related to the topic. Default is None.

    Returns:
        None
    """
    if status not in ["Generated", "Published", "In Progress", "Failed"]:
        print(
            "Invalid status. Must be one of: 'Generated', 'Published', 'In Progress', 'Failed'."
        )
        return

    topic_data = {
        "id": id,
        "title": title,
        "status": status,
        "scheduled_on": scheduled_on if scheduled_on else None,
        "generated_on": datetime.now(),
        "possible_back_links": possible_back_links if possible_back_links else None,
        "notion_link": notion_link if notion_link else None,
        "source_links": source_links if source_links else None,
        "created_by": created_by,
    }

    result = topics_collection.insert_one(topic_data)
    print(f"Topic '{title}' saved successfully with ID: {result.inserted_id}")


def save_setting_to_mongodb(id, setting_type, name, value, version=None):
    """
    Saves a setting record to the MongoDB database.

    Parameters:
        id (str): The unique identifier for the setting.
        setting_type (str): The type of the setting. Must be one of:
                            'Tone Configuration', 'Editorial Guidelines', 'API Configuration', 'Area Preferences', 'App Settings'.
        name (str): The name of the setting.
        value (str): The value of the setting.
        version (str, optional): The version of the setting. Default is None.

    Returns:
        None
    """
    if setting_type not in [
        "Tone Configuration",
        "Editorial Guidelines",
        "API Configuration",
        "Area Preferences",
        "App Settings",
    ]:
        print(
            "Invalid setting_type. Must be one of: 'Tone Configuration', 'Editorial Guidelines', 'API Configuration', 'Area Preferences', 'App Settings'."
        )
        return

    setting_data = {
        "id": id,
        "setting_type": setting_type,
        "name": name,
        "value": value,
        "version": version if version else None,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }

    result = settings_collection.insert_one(setting_data)
    print(f"Setting '{name}' saved successfully with ID: {result.inserted_id}")


def save_article_to_mongodb(id, title, file_path):
    """
    Saves an article entry to the MongoDB database.

    Parameters:
        id (str): The unique identifier for the article.
        title (str): The title of the article.
        file_path (str): The file path to the article.

    Returns:
        None
    """
    article_data = {
        "id": id,
        "title": title,
        "file_path": file_path,
        "created_at": datetime.now(),
    }

    result = articles_collection.insert_one(article_data)
    print(f"Article '{title}' saved successfully with ID: {result.inserted_id}")


# Function to insert a trusted source
def save_trusted_source_to_mongodb(id, url):
    """
    Saves a trusted source URL to the MongoDB database, ensuring the URL is unique.

    Parameters:
        id (str): The unique identifier for the trusted source.
        url (str): The URL of the trusted source.

    Returns:
        None
    """
    trusted_source_data = {
        "id": id,
        "url": url,
        "created_at": datetime.now(),
    }

    # Ensure URL uniqueness before inserting
    if trusted_sources_collection.find_one({"url": url}):
        print(f"Trusted source '{url}' already exists.")
        return

    result = trusted_sources_collection.insert_one(trusted_source_data)
    print(f"Trusted source '{url}' saved successfully with ID: {result.inserted_id}")


def save_area_preference_to_mongodb(
    id, preference_type, country=None, appointments=None
):
    """
    Saves an area preference entry to the MongoDB database.

    Parameters:
        id (str): The unique identifier for the area preference.
        preference_type (str): The type of preference. Must be one of:
                                'News Generation', 'Appointment Generation', 'App Settings'.
        country (str, optional): The country associated with the preference. Default is None.
        appointments (list, optional): A list of appointments associated with the preference. Default is None.

    Returns:
        None
    """
    if preference_type not in [
        "News Generation",
        "Appointment Generation",
        "App Settings",
    ]:
        print(
            "Invalid preference_type. Must be one of: 'News Generation', 'Appointment Generation', 'App Settings'."
        )
        return

    area_preference_data = {
        "id": id,
        "preference_type": preference_type,
        "country": country if country else None,
        "appointments": appointments if appointments else None,
        "created_at": datetime.now(),
    }

    result = area_preferences_collection.insert_one(area_preference_data)
    print(
        f"Area preference '{preference_type}' saved successfully with ID: {result.inserted_id}"
    )


def save_api_key_to_mongodb(id, key_type, api_key):
    """
    Saves an API key entry to the MongoDB database.

    Parameters:
        id (str): The unique identifier for the API key.
        key_type (str): The type of API key. Must be one of:
                        'OpenAI Key', 'Custom Search API', 'Custom Search ID', 'Browserless API'.
        api_key (str): The actual API key.

    Returns:
        None
    """
    if key_type not in [
        "OpenAI Key",
        "Custom Search API",
        "Custom Search ID",
        "Browserless API",
    ]:
        print(
            "Invalid key_type. Must be one of: 'OpenAI Key', 'Custom Search API', 'Custom Search ID', 'Browserless API'."
        )
        return

    api_key_data = {
        "id": id,
        "key_type": key_type,
        "api_key": api_key,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }

    result = api_keys_collection.insert_one(api_key_data)
    print(
        f"API key of type '{key_type}' saved successfully with ID: {result.inserted_id}"
    )


def save_search_topic_to_mongodb(topic: str, status: str = "pending"):
    """
    Saves a search topic to the MongoDB database.

    Parameters:
        topic (str): The topic to search for
        status (str): The status of the topic search (pending, completed, failed)

    Returns:
        str: The ID of the saved topic
    """
    topic_id = str(ObjectId())
    topic_data = {
        "id": topic_id,
        "topic": topic,
        "status": status,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }

    result = search_topics_collection.insert_one(topic_data)
    print(f"Search topic '{topic}' saved successfully with ID: {result.inserted_id}")
    return topic_id


def get_pending_search_topics():
    """
    Retrieves all pending search topics from MongoDB.

    Returns:
        List[Dict]: List of pending topics
    """
    return list(search_topics_collection.find({"status": "pending"}))


def update_search_topic_status(topic_id: str, status: str):
    """
    Updates the status of a search topic.

    Parameters:
        topic_id (str): The ID of the topic to update
        status (str): The new status
    """
    search_topics_collection.update_one(
        {"id": topic_id}, {"$set": {"status": status, "updated_at": datetime.now()}}
    )


def save_french_blog_to_mongodb(
    collection_id,
    blog_content,
    blog_title,
    blog_published_date,
):
    """
    Saves a generated French blog to the MongoDB database.

    Parameters:
        collection_id (str): The ID of the parent collection
        blog_content (str): The content of the French blog
        blog_title (str): The title of the blog (can be in English or French)
        blog_published_date (datetime): The publication date of the blog (required)

    Returns:
        str: The ID of the saved blog
    """
    # Extract headings from the content using markdown format
    headings = []
    for line in blog_content.split("\n"):
        if line.startswith("#"):
            headings.append(line.strip("# "))

    blog_data = {
        "collection_id": collection_id,
        "title": {
            "original": blog_title,  # Original title (can be English)
            "french": (
                blog_title
                if blog_title.startswith("Analyse:")
                else f"Analyse: {blog_title}"
            ),  # Ensure French format
        },
        "content": blog_content,
        "headings": headings,  # Store extracted headings
        "published_date": blog_published_date,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "status": "draft",  # Default status for new blogs
        "metadata": {"has_headings": len(headings) > 0, "heading_count": len(headings)},
    }

    result = french_blogs_collection.insert_one(blog_data)
    print(f"French blog saved successfully with ID: {result.inserted_id}")
    return str(result.inserted_id)


mongo_tools = [
    Tool.from_function(
        name="save_french_tips",
        func=save_french_tips_to_mongodb,
        description="Saves a french tips to the database. Takes 'id', 'french_tips'.",
    ),
    Tool.from_function(
        name="save_user",
        func=save_user_to_mongodb,
        description="Saves a user to the database. Takes 'username', 'email', 'password','otp'.",
    ),
    Tool.from_function(
        name="save_news",
        func=save_news_to_mongodb,
        description="Saves a news item to the database. Takes 'title', 'status', 'source_links', and 'notion_link'.",
    ),
    Tool.from_function(
        name="save_quality_metrics",
        func=save_quality_metrics_to_mongodb,
        description="Saves quality metrics for news or user-generated content. Takes 'parent_id', 'parent_type', 'human_writing_score', 'plagiarism_score', 'fact_verification', and 'trusted_source_score'.",
    ),
    Tool.from_function(
        name="save_generation_log",
        func=save_generation_log_to_mongodb,
        description="Saves a generation log entry for a news item or insight. Takes 'parent_id', 'parent_type', 'sources_analyzed', 'sources_used', 'source_titles', 'source_links', and 'time_spent'.",
    ),
    Tool.from_function(
        name="save_tip_sheet",
        func=save_tip_sheet_to_mongodb,
        description="Saves a tip sheet. Takes 'id', 'parent_id', 'parent_type', and 'final_bullet_points'.",
    ),
    Tool.from_function(
        name="save_questions",
        func=save_questions_to_mongo,
        description="Saves a question entry. Takes 'id', 'parent_id', 'parent_type', 'question_text','time_spent'.",
    ),
    Tool.from_function(
        name="save_answer_plan",
        func=save_answer_plan_to_mongodb,
        description="Saves an answer plan. Takes 'id', 'question_id', 'version', and 'plan_text'.",
    ),
    Tool.from_function(
        name="save_feedback",
        func=save_feedback_to_mongodb,
        description="Saves feedback for an answer plan. Takes 'id', 'answer_plan_id', and 'feedback_text'.",
    ),
    Tool.from_function(
        name="save_final_result",
        func=save_final_result_to_mongodb,
        description="Saves a final result for a question. Takes 'id', 'question_id', and 'bullet_points'.",
    ),
    Tool.from_function(
        name="save_nomination",
        func=save_nomination_to_mongodb,
        description="Saves a nomination entry. Takes 'id', 'title', 'sources_link', 'appointee', and 'status'.",
    ),
    Tool.from_function(
        name="save_insight",
        func=save_insight_to_mongodb,
        description="Saves an insight entry. Takes 'title', 'scheduled_on','status', 'source_links','possible_back_links', 'notion_link'.",
    ),
    Tool.from_function(
        name="save_insight_keyword",
        func=save_insight_keyword_to_mongodb,
        description="Saves a keyword related to an insight. Takes 'id', 'insight_id', 'keyword', and 'keyword_type'.",
    ),
    Tool.from_function(
        name="save_insight_metadata",
        func=save_insight_metadata_to_mongodb,
        description="Saves metadata for an insight. Takes 'id', 'insight_id','used_keywords', 'possible_back_links'.",
    ),
    Tool.from_function(
        name="save_topic",
        func=save_topic_to_mongodb,
        description="Saves a topic entry. Takes 'id', 'title', 'status', 'created_by','scheduled_on', 'possible_back_links', 'notion_link', 'source_links'.",
    ),
    Tool.from_function(
        name="save_setting",
        func=save_setting_to_mongodb,
        description="Saves a setting record. Takes 'id', 'setting_type', 'name', 'value','version'.",
    ),
    Tool.from_function(
        name="save_article",
        func=save_article_to_mongodb,
        description="Saves an article entry. Takes 'id', 'title', and 'file_path'.",
    ),
    Tool.from_function(
        name="save_trusted_source",
        func=save_trusted_source_to_mongodb,
        description="Saves a trusted source URL. Takes 'id' and 'url'.",
    ),
    Tool.from_function(
        name="save_area_preference",
        func=save_area_preference_to_mongodb,
        description="Saves an area preference entry. Takes 'id', 'preference_type','country', 'appointments'.",
    ),
    Tool.from_function(
        name="save_api_key",
        func=save_api_key_to_mongodb,
        description="Saves an API key. Takes 'id', 'key_type', and 'api_key'.",
    ),
    Tool.from_function(
        name="save_search_topic",
        func=save_search_topic_to_mongodb,
        description="Saves a search topic to the database. Takes 'topic' and optional 'status'.",
    ),
    Tool.from_function(
        name="get_pending_topics",
        func=get_pending_search_topics,
        description="Retrieves all pending search topics from the database.",
    ),
    Tool.from_function(
        name="update_topic_status",
        func=update_search_topic_status,
        description="Updates the status of a search topic. Takes 'topic_id' and 'status'.",
    ),
    Tool.from_function(
        name="save_french_blog",
        func=save_french_blog_to_mongodb,
        description="Saves a generated French blog to the database. Takes 'collection_id', 'blog_content', 'blog_title', and 'blog_published_date'.",
    ),
]
