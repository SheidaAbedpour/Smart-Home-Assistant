from datetime import datetime
from typing import List
from smart_home.devices.base_device import SmartHomeDevice


class SmartTelevision(SmartHomeDevice):
    """Smart TV with channel, volume, and input control"""

    MIN_CHANNEL = 1
    MAX_CHANNEL = 999
    MIN_VOLUME = 0
    MAX_VOLUME = 100

    VALID_INPUTS = ["hdmi1", "hdmi2", "hdmi3", "usb", "cable", "antenna", "netflix", "youtube"]
    INPUT_EMOJIS = {
        "hdmi1": "🔌", "hdmi2": "🔌", "hdmi3": "🔌", "usb": "🔌",
        "cable": "📡", "antenna": "📡", "netflix": "🎬", "youtube": "📹"
    }

    def __init__(self, location: str, default_volume: int = 50, default_channel: int = 1):
        initial_state = {
            "power": False,
            "channel": default_channel,
            "volume": default_volume,
            "input": "hdmi1"
        }
        super().__init__(f"{location} TV", location, "tv", initial_state)

    def set_channel(self, channel: int) -> str:
        """Set TV channel with validation"""
        if not self.is_online:
            return f"❌ {self.name} is offline"

        if not self.state.get("power"):
            return f"❌ {self.name} is off. Turn it on first"

        try:
            channel = max(self.MIN_CHANNEL, min(self.MAX_CHANNEL, int(channel)))
            self.state["channel"] = channel
            self.last_updated = datetime.now()
            return f"📺 {self.name} channel changed to {channel}"

        except (ValueError, TypeError):
            return f"❌ Invalid channel. Please use {self.MIN_CHANNEL}-{self.MAX_CHANNEL}"

    def set_volume(self, volume: int) -> str:
        """Set TV volume with validation"""
        if not self.is_online:
            return f"❌ {self.name} is offline"

        if not self.state.get("power"):
            return f"❌ {self.name} is off. Turn it on first"

        try:
            volume = max(self.MIN_VOLUME, min(self.MAX_VOLUME, int(volume)))
            self.state["volume"] = volume
            self.last_updated = datetime.now()

            emoji = "🔇" if volume == 0 else "🔈" if volume <= 30 else "🔉" if volume <= 70 else "🔊"
            return f"{emoji} {self.name} volume set to {volume}"

        except (ValueError, TypeError):
            return f"❌ Invalid volume. Please use {self.MIN_VOLUME}-{self.MAX_VOLUME}"

    def set_input(self, input_source: str) -> str:
        """Set TV input with validation"""
        if not self.is_online:
            return f"❌ {self.name} is offline"

        if not self.state.get("power"):
            return f"❌ {self.name} is off. Turn it on first"

        input_normalized = input_source.lower().strip()

        if input_normalized in self.VALID_INPUTS:
            self.state["input"] = input_normalized
            self.last_updated = datetime.now()
            emoji = self.INPUT_EMOJIS.get(input_normalized, "📺")
            return f"{emoji} {self.name} input changed to {input_normalized}"

        return f"❌ Invalid input. Available: {', '.join(self.VALID_INPUTS)}"

    def get_status(self) -> str:
        """Get formatted TV status"""
        if not self.is_online:
            return f"{self.name} ({self.location}): OFFLINE 🔴"

        if self.state.get("power"):
            volume = self.state.get("volume", 50)
            volume_emoji = "🔇" if volume == 0 else "🔈" if volume <= 30 else "🔉" if volume <= 70 else "🔊"
            input_emoji = self.INPUT_EMOJIS.get(self.state.get("input"), "📺")

            return (f"{self.name} ({self.location}): ON 🟢 - "
                    f"Channel {self.state.get('channel')} 📺, "
                    f"Volume {volume} {volume_emoji}, "
                    f"Input: {self.state.get('input')} {input_emoji}")

        return f"{self.name} ({self.location}): OFF 🔴"
