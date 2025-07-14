import requests
import logging
from typing import Optional
from smart_home.config import config

logger = logging.getLogger(__name__)


class NewsService:
    """News headlines service"""

    def __init__(self):
        """Initialize news service"""
        self.api_key = config.news_api_key
        self.api_url = "https://newsapi.org/v2/top-headlines"

        if config.is_news_configured():
            logger.info("News service initialized")
        else:
            logger.warning("News API key not configured")

    def get_news(self, category: str = "technology", country: str = "us") -> str:
        """Get latest news headlines"""
        if not self.api_key:
            return ("❌ News API not configured. Please add NEWS_API_KEY to your .env file.\n"
                    "Get your free API key from: https://newsapi.org/")

        try:
            params = {
                "apiKey": self.api_key,
                "category": category,
                "country": country,
                "pageSize": 5
            }

            response = requests.get(self.api_url, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()
                return self._format_news_response(data, category)
            elif response.status_code == 401:
                return "❌ Invalid news API key. Please check your NEWS_API_KEY"
            elif response.status_code == 429:
                return "❌ News API rate limit exceeded. Please try again later"
            else:
                return f"❌ News service error (Code: {response.status_code})"

        except requests.exceptions.Timeout:
            return "❌ News request timed out. Please try again"
        except requests.exceptions.ConnectionError:
            return "❌ Cannot connect to news service. Check your internet connection"
        except Exception as e:
            logger.error(f"News API error: {e}")
            return f"❌ News service error: {str(e)}"

    def _format_news_response(self, data: dict, category: str) -> str:
        """Format news data into user-friendly string"""
        try:
            if not data.get('articles'):
                return f"❌ No news articles found for {category} category"

            category_emojis = {
                "technology": "💻", "business": "💼", "sports": "⚽",
                "health": "🏥", "science": "🔬", "general": "📰", "entertainment": "🎬"
            }
            emoji = category_emojis.get(category, "📰")

            headlines = [f"{emoji} Latest {category.capitalize()} Headlines:"]

            for i, article in enumerate(data['articles'][:5], 1):
                title = article['title']
                source = article['source']['name']
                headlines.append(f"   {i}. {title} ({source})")

            return "\n".join(headlines)
        except Exception as e:
            logger.error(f"Error formatting news data: {e}")
            return f"❌ Error formatting news data"
