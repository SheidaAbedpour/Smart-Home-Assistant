from datetime import datetime
from typing import List
from smart_home.devices.base_device import SmartHomeDevice


class SmartLamp(SmartHomeDevice):
    """Smart Lamp with brightness and color control"""

    VALID_COLORS = ["white", "red", "blue", "green", "yellow", "purple", "orange"]
    COLOR_EMOJIS = {
        "white": "⚪", "red": "🔴", "blue": "🔵", "green": "🟢",
        "yellow": "🟡", "purple": "🟣", "orange": "🟠"
    }

    def __init__(self, location: str, default_brightness: int = 100, default_color: str = "white"):
        initial_state = {
            "power": False,
            "brightness": default_brightness,
            "color": default_color
        }
        super().__init__(f"{location} Lamp", location, "lamp", initial_state)

    def set_brightness(self, level: int) -> str:
        """Set lamp brightness with validation"""
        if not self.is_online:
            return f"❌ {self.name} is offline"

        if not self.state.get("power"):
            return f"❌ {self.name} is off. Turn it on first"

        try:
            level = max(0, min(100, int(level)))

            if level == 0:
                self.state["brightness"] = 0
                self.state["power"] = False
                return f"🌙 {self.name} dimmed to 0% (turned off)"

            self.state["brightness"] = level
            self.last_updated = datetime.now()
            return f"💡 {self.name} brightness set to {level}%"

        except (ValueError, TypeError):
            return f"❌ Invalid brightness value. Please use 0-100"

    def set_color(self, color: str) -> str:
        """Set lamp color with validation"""
        if not self.is_online:
            return f"❌ {self.name} is offline"

        if not self.state.get("power"):
            return f"❌ {self.name} is off. Turn it on first"

        color_normalized = color.lower().strip()

        if color_normalized in self.VALID_COLORS:
            self.state["color"] = color_normalized
            self.last_updated = datetime.now()
            emoji = self.COLOR_EMOJIS.get(color_normalized, "💡")
            return f"{emoji} {self.name} color changed to {color_normalized}"

        return f"❌ Invalid color. Available: {', '.join(self.VALID_COLORS)}"

    def get_status(self) -> str:
        """Get formatted lamp status"""
        if not self.is_online:
            return f"{self.name} ({self.location}): OFFLINE 🔴"

        if self.state.get("power"):
            color_emoji = self.COLOR_EMOJIS.get(self.state.get("color"), "💡")
            return (f"{self.name} ({self.location}): ON 🟢 - "
                    f"{self.state.get('brightness')}% brightness "
                    f"{color_emoji} {self.state.get('color')} color")

        return f"{self.name} ({self.location}): OFF 🔴"

    @classmethod
    def get_valid_colors(cls) -> List[str]:
        """Get list of valid colors"""
        return cls.VALID_COLORS.copy()
