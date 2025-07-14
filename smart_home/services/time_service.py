import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class TimeService:
    """Time and date service"""

    @staticmethod
    def get_current_time() -> str:
        """Get current date and time with emoji"""
        try:
            now = datetime.now()
            formatted_time = now.strftime("%A, %B %d, %Y at %I:%M %p")
            timezone_info = now.astimezone().tzname()

            # Time-based emoji
            hour = now.hour
            if 6 <= hour < 12:
                emoji = "🌅"  # Morning
            elif 12 <= hour < 17:
                emoji = "☀️"  # Afternoon
            elif 17 <= hour < 21:
                emoji = "🌇"  # Evening
            else:
                emoji = "🌙"  # Night

            return f"🕒 Current time: {formatted_time} ({timezone_info}) {emoji}"
        except Exception as e:
            logger.error(f"Error getting time: {e}")
            return f"❌ Error getting current time: {str(e)}"
