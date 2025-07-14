import os
from dataclasses import dataclass, field
from typing import List
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    # API Keys
    groq_api_key: str = field(default_factory=lambda: os.getenv("GROQ_API_KEY", ""))
    weather_api_key: str = field(default_factory=lambda: os.getenv("WEATHER_API_KEY", ""))
    news_api_key: str = field(default_factory=lambda: os.getenv("NEWS_API_KEY", ""))

    # Device Configuration
    lamps: List[str] = field(default_factory=lambda: ["Kitchen", "Bathroom", "Room 1", "Room 2"])
    acs: List[str] = field(default_factory=lambda: ["Room 1", "Kitchen"])
    tvs: List[str] = field(default_factory=lambda: ["Living Room"])

    # Voice Configuration
    wake_words: List[str] = field(default_factory=lambda: ["hey assistant", "assistant"])

    # Application Settings
    debug: bool = field(default_factory=lambda: os.getenv("DEBUG", "False").lower() == "true")
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    default_city: str = field(default_factory=lambda: os.getenv("DEFAULT_CITY", "Tehran"))

    def is_groq_configured(self) -> bool:
        """Check if Groq API is configured"""
        return bool(self.groq_api_key and self.groq_api_key != "your_groq_api_key_here")

    def is_weather_configured(self) -> bool:
        """Check if Weather API is configured"""
        return bool(self.weather_api_key and self.weather_api_key != "your_weather_api_key")

    def is_news_configured(self) -> bool:
        """Check if News API is configured"""
        return bool(self.news_api_key and self.news_api_key != "your_news_api_key")


# Global config instance
my_config = Config()
