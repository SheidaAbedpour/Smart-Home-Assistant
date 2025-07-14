import requests
import logging
from typing import Optional
from smart_home.config import config

logger = logging.getLogger(__name__)


class WeatherService:
    """Weather information service"""

    def __init__(self):
        """Initialize weather service"""
        self.api_key = config.weather_api_key
        self.api_url = "http://api.openweathermap.org/data/2.5/weather"

        if config.is_weather_configured():
            logger.info("Weather service initialized")
        else:
            logger.warning("Weather API key not configured")

    def get_weather(self, city: str = None) -> str:
        """Get current weather information"""
        city = city or config.default_city

        if not self.api_key:
            return ("❌ Weather API not configured. Please add WEATHER_API_KEY to your .env file.\n"
                    "Get your free API key from: https://openweathermap.org/api")

        try:
            params = {
                "q": city,
                "appid": self.api_key,
                "units": "metric"
            }

            response = requests.get(self.api_url, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()
                return self._format_weather_response(data, city)
            elif response.status_code == 401:
                return "❌ Invalid weather API key. Please check your WEATHER_API_KEY"
            elif response.status_code == 404:
                return f"❌ City '{city}' not found. Please check the spelling"
            else:
                return f"❌ Weather service error (Code: {response.status_code})"

        except requests.exceptions.Timeout:
            return "❌ Weather request timed out. Please try again"
        except requests.exceptions.ConnectionError:
            return "❌ Cannot connect to weather service. Check your internet connection"
        except Exception as e:
            logger.error(f"Weather API error: {e}")
            return f"❌ Weather service error: {str(e)}"

    def _format_weather_response(self, data: dict, city: str) -> str:
        """Format weather data into user-friendly string"""
        try:
            temp = round(data['main']['temp'], 1)
            description = data['weather'][0]['description'].title()
            humidity = data['main']['humidity']
            feels_like = round(data['main']['feels_like'], 1)

            # Weather emoji based on condition
            weather_id = data['weather'][0]['id']
            emoji = self._get_weather_emoji(weather_id)

            return (f"{emoji} Weather in {city}:\n"
                    f"🌡️ Temperature: {temp}°C (feels like {feels_like}°C)\n"
                    f"🌤️ Conditions: {description}\n"
                    f"💧 Humidity: {humidity}%")
        except Exception as e:
            logger.error(f"Error formatting weather data: {e}")
            return f"❌ Error formatting weather data"

    def _get_weather_emoji(self, weather_id: int) -> str:
        """Get emoji based on weather condition"""
        if weather_id < 300:
            return "⛈️"  # Thunderstorm
        elif weather_id < 400:
            return "🌦️"  # Drizzle
        elif weather_id < 600:
            return "🌧️"  # Rain
        elif weather_id < 700:
            return "❄️"  # Snow
        elif weather_id < 800:
            return "🌫️"  # Fog/Mist
        elif weather_id == 800:
            return "☀️"  # Clear
        else:
            return "☁️"  # Clouds
