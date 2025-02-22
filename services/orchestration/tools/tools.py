import requests
import os
from bs4 import BeautifulSoup
from langchain_community.chat_models import ChatOpenAI
from langchain.agents import initialize_agent, AgentType
from langchain.tools import Tool
from typing import List, Dict, Any
from pydantic import BaseModel, Field
import logging
from googlesearch import search

# Define news sources
AFRICA_NEWS_SITES = [
    "https://apnews.com/hub/africa",
    "https://www.thetimes.com/world/africa/",
    "https://www.reuters.com/world/africa/",
    "https://www.ft.com/middle-east-north-africa",
    "https://african.business/",
    "https://www.africanews.com/business/",
    "https://www.banquemondiale.org/fr/region/afr",
]


class NewsArticle(BaseModel):
    headline: str = Field(..., description="The headline of the news article")
    summary: str = Field(..., description="A brief summary of the article")
    url: str = Field(..., description="The URL of the article")
    source: str = Field(..., description="The source website of the article")


def scrape_news_site(url: str) -> List[str]:
    """
    Scrapes article links from a news website.

    Args:
        url (str): The URL of the news website to scrape.

    Returns:
        List[str]: List of article URLs.
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            links = []

            # Different selectors for different sites
            if "apnews.com" in url:
                links = [a["href"] for a in soup.select("ul li a") if "href" in a.attrs]
                links = [
                    link
                    for link in links
                    if link.startswith("https://apnews.com/article/")
                ]
            elif "reuters.com" in url:
                links = [
                    a["href"]
                    for a in soup.select("a[href*='/article/']")
                    if "href" in a.attrs
                ]
                links = [
                    (
                        f"https://www.reuters.com{link}"
                        if not link.startswith("http")
                        else link
                    )
                    for link in links
                ]
            elif "african.business" in url:
                links = [
                    a["href"] for a in soup.select("article a") if "href" in a.attrs
                ]
            elif "africanews.com" in url:
                links = [
                    a["href"]
                    for a in soup.select(".just-in__article a")
                    if "href" in a.attrs
                ]
            else:
                # Generic link extraction
                links = [a["href"] for a in soup.find_all("a") if "href" in a.attrs]
                links = [
                    link for link in links if "/article/" in link or "/news/" in link
                ]

            # Ensure all links are absolute URLs
            links = [
                link if link.startswith("http") else f"{url.rstrip('/')}{link}"
                for link in links
            ]
            return list(set(links))[:3]  # Return up to 3 unique links per source

    except Exception as e:
        logging.error(f"Error scraping {url}: {str(e)}")
        return []

    return []


def fetch_article_details(url: str) -> Dict[str, str]:
    """
    Fetches details of a single article.

    Args:
        url (str): The URL of the article to scrape.

    Returns:
        Dict[str, str]: Dictionary containing article details.
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")

            # Try different selectors for headline
            headline = None
            for selector in ["h1", ".article-headline", ".article-title", ".headline"]:
                headline_elem = soup.select_one(selector)
                if headline_elem:
                    headline = headline_elem.text.strip()
                    break

            if not headline:
                headline = "No headline found"

            # Try different selectors for summary/content
            paragraphs = []
            for selector in [
                "article p",
                ".article-body p",
                ".content p",
                ".story-body p",
            ]:
                paragraphs = soup.select(selector)
                if paragraphs:
                    break

            summary = (
                " ".join([p.text.strip() for p in paragraphs[:2]])
                if paragraphs
                else "No summary available."
            )

            # Determine source from URL
            source = url.split("/")[2]

            return NewsArticle(
                headline=headline, summary=summary, url=url, source=source
            ).model_dump()

    except Exception as e:
        logging.error(f"Error fetching article {url}: {str(e)}")
        return None

    return None


def get_latest_africa_news(_: str = "") -> List[Dict[str, str]]:
    """
    Tool for fetching the latest news articles from multiple African news sources.

    Args:
        _: Placeholder parameter for LangChain compatibility

    Returns:
        List[Dict[str, str]]: List of articles with their headlines, summaries, URLs, and sources
    """
    all_articles = []

    # Scrape each news site
    for site_url in AFRICA_NEWS_SITES:
        try:
            article_urls = scrape_news_site(site_url)
            for url in article_urls:
                article = fetch_article_details(url)
                if article:
                    all_articles.append(article)
        except Exception as e:
            logging.error(f"Error processing site {site_url}: {str(e)}")
            continue

    return all_articles


def search_topic_news(topic: str, num_results: int = 10) -> List[str]:
    """
    Search for news articles about a specific topic using Google Search.

    Args:
        topic (str): The topic to search for
        num_results (int): Number of results to return

    Returns:
        List[str]: List of article URLs
    """
    search_query = f"{topic} news Africa"
    try:
        # Use Google Search to find relevant articles
        search_results = search(
            search_query,
            stop=num_results,  # Only use stop parameter
            pause=2.0,
            extra_params={"tbm": "nws"},  # Limit to news articles
        )
        return list(search_results)
    except Exception as e:
        logging.error(f"Error searching for topic {topic}: {str(e)}")
        return []


def get_topic_news(topic: str = "") -> List[Dict[str, str]]:
    """
    Tool for fetching news articles about a specific topic.

    Args:
        topic (str): The topic to search for

    Returns:
        List[Dict[str, str]]: List of articles with their headlines, summaries, URLs, and sources
    """
    all_articles = []

    try:
        # Get article URLs for the topic
        article_urls = search_topic_news(topic)

        # Fetch details for each article
        for url in article_urls:
            article = fetch_article_details(url)
            if article:
                all_articles.append(article)

    except Exception as e:
        logging.error(f"Error processing topic {topic}: {str(e)}")

    return all_articles


# Create the LangChain tool
news_tool = Tool(
    name="get_africa_news",
    description="Fetches the latest news articles from multiple African news sources. Returns a list of articles with headlines, summaries, URLs, and sources.",
    func=get_latest_africa_news,
)

# Create the topic news tool
topic_news_tool = Tool(
    name="get_topic_news",
    description="Fetches news articles about a specific topic from various sources. Returns a list of articles with headlines, summaries, URLs, and sources.",
    func=get_topic_news,
)

# Example of how to use the tools
if __name__ == "__main__":
    # Test the general news tool
    print("Latest general news articles:", get_latest_africa_news())

    # Test the topic-specific tool
    topic = "digital banking"
    print(f"\nNews articles about {topic}:", get_topic_news(topic))

#
# This function is used to generate the questions from the Headline and summary from the previous tool function.
#

# def analyze_and_generate_questions(query: str) -> list:
#     """
#     Analyzes the given headlines and summaries and generates relevant blog questions.

#     Args:
#         input_data (list): List of dictionaries containing "headline", "summary", and "url".

#     Returns:
#         List of generated questions for blog content.
#     """

#     input_data = fetch_apnews_articles(query)
#     # Debugging: Print input_data to confirm its structure
#     print("Input data:", input_data)  # Debug line

#     # Ensure input_data is a list of dictionaries and contains the expected keys
#     if isinstance(input_data, list) and all(
#         isinstance(item, dict) and 'headline' in item and 'summary' in item and 'url' in item for item in input_data
#     ):
#         # Format input as a string for LLM
#         formatted_input = "\n".join([f"Headline: {article['headline']}\nSummary: {article['summary']}\nURL: {article['url']}" for article in input_data])

#         prompt = f"""
#         Given the following news articles, generate insightful blog discussion questions:

#         {formatted_input}

#         The questions should be open-ended, engaging, and thought-provoking.
#         """

#         response = llm.predict(prompt)
#         return response.split("\n")
#     else:
#         return ["Error: The input data is not formatted correctly. Ensure it is a list of dictionaries with 'headline', 'summary', and 'url' keys."]
