from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Union
import requests
import time
import base64
import uuid
import json
import os
import random
from dotenv import load_dotenv
from openai import OpenAI

from pymongo import MongoClient

from services.orchestration.tools.mongo import mongo_tools
from services.logger_service import LoggerUtils, LogLevel
from services.orchestration.tools.tools import news_tool

logger = LoggerUtils("quality_metrics", LogLevel.DEBUG)

# client = OpenAI()

from factory import OPENAI_CLIENT

client = OpenAI(api_key=OPENAI_CLIENT.api_key)

# MongoDB connection setup
mongo_client = MongoClient(
    "mongodb+srv://aipress:fBbd6GOgUyzP96uI@cluster0.6sgjy.mongodb.net/"
)  # Replace with your MongoDB connection URI

# Secure credential handling
COPYLEAKS_EMAIL = os.getenv("COPYLEAKS_EMAIL")
COPYLEAKS_API_KEY = os.getenv("COPYLEAKS_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

tools = [news_tool] + [
    tool for tool in mongo_tools if tool.name in ["save_quality_metrics"]
]


# Request and Response Models
class TextAnalysisRequest(BaseModel):
    text: str = Field(..., min_length=1, description="The text to analyze")
    webhook_url: Optional[str] = Field(
        None, description="Optional webhook URL for async results"
    )


class PlagiarismResult(BaseModel):
    plagiarism_score: Union[float, str]
    sources: List[Dict] = []


class AIDetectionResult(BaseModel):
    ai_content_score: int
    human_writing_score: int
    reason: str


class PlagiarismSource(BaseModel):
    url: str
    similarity: float


class PlagiarismCheck(BaseModel):
    plagiarism_score: Optional[int]
    sources: List[PlagiarismSource]
    trusted_source_score: Optional[int]


class FactVerification(BaseModel):
    fact_verification: bool
    analysis: str


class AnalysisResponse(BaseModel):
    plagiarism_check: Union[PlagiarismResult, Dict[str, str]]
    ai_detection: Dict
    fact_verification: FactVerification


def get_copyleaks_token():
    """Get authentication token from Copyleaks API."""
    url = "https://id.copyleaks.com/v3/account/login/api"
    data = {"email": COPYLEAKS_EMAIL, "key": COPYLEAKS_API_KEY}

    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
        return response.json().get("access_token")
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication Error: {str(e)}",
        )


# Function to check plagiarism using Copyleaks API
def check_plagiarism(text):
    """Check plagiarism using Copyleaks API."""
    print("------------------> Inside check_plagiarism")
    if not COPYLEAKS_API_KEY:
        raise HTTPException(status_code=400, detail="Missing Copyleaks API Key")

    url = " https://api.copyleaks.com"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {COPYLEAKS_API_KEY}",
    }
    data = {"text": text, "includeHtml": False}
    print("Data ----------------->", data)
    try:
        print("------------------> Inside check_plagiarism before response")
        response = requests.post(url, json=data, headers=headers)
        print("------------------> Inside check_plagiarism after response")
        if response.status_code == 200:
            result = response.json()
            plagiarism_score = result.get("plagiarism_score", "N/A")
            sources = result.get("sources", [])
            return {"Plagiarism_Score": plagiarism_score, "Sources": sources}
        else:
            return {
                "error": "Failed to retrieve plagiarism data",
                "status_code": response.status_code,
            }

    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {str(e)}"}


# Function to detect AI-generated content using OpenAI
def detect_ai_content(text):
    """Detect if the given text is AI-generated using OpenAI GPT-4."""

    if not OPENAI_API_KEY:
        raise HTTPException(status_code=400, detail="Missing OpenAI API Key")

    # Construct AI evaluation prompt
    prompt = (
        "Analyze the following text to determine if it's AI-generated or human-written. "
        "Evaluate based on these indicators:\n"
        "1. Coherence/Consistency - AI text often has perfect structure but may lack depth\n"
        "2. Creativity/Originality - Humans tend to use unique metaphors/personal experiences\n"
        "3. Error Patterns - Look for unnatural phrasing or overly formal tone\n"
        "4. Context Handling - Humans better maintain long-term context in complex narratives\n"
        "5. Repetition Patterns - AI may repeat phrases with slight variations\n"
        "6. Common AI Phrases - Identify phrases like 'it's important to note' or 'however, it's crucial'\n\n"
        "Provide:\n"
        "- AI_Content_Score (0-100): Probability of AI generation\n"
        "- Human_Writing_Score (0-100): Probability of human authorship\n"
        "- Reason: Concise analysis using the above indicators\n\n"
        "Rules:\n"
        "1. Scores must sum to 100\n"
        "2. Be cautious with technical/scientific content\n"
        "3. Consider domain-specific jargon\n"
        "4. Account for possible human editing of AI content\n\n"
        "Format response as valid JSON without markdown:\n"
        '{"AI_Content_Score": X, "Human_Writing_Score": Y, "Reason": "..."}\n\n'
        f"Text to analyze: {text}"
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "You are an AI content detection assistant.",
                },
                {"role": "user", "content": prompt},
            ],
        )

        result = response.choices[0].message.content.strip()

        # Extract only Human_Writing_Score
        result_json = json.loads(result)
        human_writing_score = result_json.get("Human_Writing_Score", "N/A")

        return human_writing_score

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"OpenAI API request failed: {str(e)}"
        )

def trusted_source_score():
    trusted_domains = [
        ".gov",
        ".edu",
        "bbc.com",
        "nytimes.com",
        "researchgate.net",
        "theguardian.com",
        "thetimes.co.uk",
        "reuters.com",
        "worldbank.org",
        "legit.ng",
        "zawya.com",
        "businessday.ng",
        "aljazeera.com",
        "ft.com",
        "nairametrics.com",
        "africanews.com",
        "businessdailyafrica.com",
        "cnbcafrica.com",
    ]

    db = mongo_client["ericDb"]  # Replace with your actual database name
    generation_logs_collection = db["generation_logs"]

    logs = generation_logs_collection.find(
        {}, {"source_link": 1, "_id": 0}
    )  # Fetch only 'source_link' field
    sources = [log["source_link"] for log in logs if "source_link" in log]

    if not sources:
        return 0  # No sources found

    # Count how many URLs belong to trusted domains
    trusted_count = sum(
        1 for url in sources if any(domain in url for domain in trusted_domains)
    )

    # Calculate the trust percentage
    return (trusted_count / len(sources)) * 100


def verify_facts(article_content):
    """
    Function to verify if the facts in the given article content are accurate.
    Returns True if verified, False otherwise.
    """
    prompt = f"""
    You are a fact-checking assistant. Your task is to verify the accuracy of the claims in the given article.
    Analyze the content, check for factual inconsistencies, and compare it with reliable sources.
    
    Respond in the following format:
    
    - Factually Accurate: (true/false)
    - Reasoning: [Provide a brief explanation for your assessment]
    
    Here is the article content:
    {article_content}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert in fact verification.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=200,
        )

        # Correct way to access the response content
        result = response.choices[0].message.content.strip()

        # Extract the fact verification result
        factually_accurate = "true" in result.lower()

        return {"fact_verification": factually_accurate, "analysis": result}

    except Exception as e:
        return {"error": f"Fact verification failed: {str(e)}"}


def blog_quality_metrics(blog_generation, collection_id):
    """
    Analyze text for AI-generated content and fact verification.

    Parameters:
    - blog_generation: The blog text to analyze
    - collection_id: The ID of the collection

    Returns:
    - Combined results of AI detection and fact verification
    """
    try:
        print("------------------> Inside blog quality metrics")
        ai_detection_result = detect_ai_content(blog_generation)
        fact_verification_result = verify_facts(blog_generation)
        source_score = trusted_source_score()

        save_quality_metrics_tool = next(
            tool for tool in tools if tool.name == "save_quality_metrics"
        )

        try:
            # Save metrics to MongoDB using the tool
            feedback_id = str(uuid.uuid4())
            save_quality_metrics_tool.func(
                parent_id=collection_id,
                parent_type="metrics",
                human_writing_score=ai_detection_result,
                plagiarism_score=0,  # Set to 0 since we're not checking plagiarism
                fact_verification=fact_verification_result,
                trusted_source_score=source_score,
            )
            logger.debug(f"Saved quality metrics to MongoDB with ID: {feedback_id}")
        except Exception as e:
            logger.error(f"Error saving metrics to MongoDB: {str(e)}")

        return {
            "ai_detection": ai_detection_result,
            "fact_verification": fact_verification_result,
            "trusted_source_score": source_score,
        }
    except Exception as e:
        logger.error(f"Error in blog quality metrics: {str(e)}")
        raise
