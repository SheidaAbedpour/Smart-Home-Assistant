from datetime import datetime
from typing import List
from smart_home.devices.base_device import SmartHomeDevice


class SmartAirConditioner(SmartHomeDevice):
    """Smart AC with temperature, mode, and fan speed control"""

    MIN_TEMPERATURE = 16
    MAX_TEMPERATURE = 30
    VALID_MODES = ["cool", "heat", "fan", "auto", "dry"]
    VALID_FAN_SPEEDS = ["low", "medium", "high", "auto"]

    MODE_EMOJIS = {
        "cool": "❄️", "heat": "🔥", "fan": "💨",
        "auto": "🔄", "dry": "💧"
    }

    def __init__(self, location: str, default_temperature: int = 22,
                 default_mode: str = "cool", default_fan_speed: str = "medium"):
        initial_state = {
            "power": False,
            "temperature": default_temperature,
            "mode": default_mode,
            "fan_speed": default_fan_speed
        }
        super().__init__(f"{location} AC", location, "ac", initial_state)

    def set_temperature(self, temp: int) -> str:
        """Set AC temperature with validation"""
        if not self.is_online:
            return f"❌ {self.name} is offline"

        if not self.state.get("power"):
            return f"❌ {self.name} is off. Turn it on first"

        try:
            temp = max(self.MIN_TEMPERATURE, min(self.MAX_TEMPERATURE, int(temp)))
            self.state["temperature"] = temp
            self.last_updated = datetime.now()

            emoji = "❄️" if temp <= 20 else "🔥" if temp >= 25 else "🌡️"
            return f"{emoji} {self.name} temperature set to {temp}°C"

        except (ValueError, TypeError):
            return f"❌ Invalid temperature. Please use {self.MIN_TEMPERATURE}-{self.MAX_TEMPERATURE}°C"

    def set_mode(self, mode: str) -> str:
        """Set AC mode with validation"""
        if not self.is_online:
            return f"❌ {self.name} is offline"

        if not self.state.get("power"):
            return f"❌ {self.name} is off. Turn it on first"

        mode_normalized = mode.lower().strip()

        if mode_normalized in self.VALID_MODES:
            self.state["mode"] = mode_normalized
            self.last_updated = datetime.now()
            emoji = self.MODE_EMOJIS.get(mode_normalized, "❄️")
            return f"{emoji} {self.name} mode set to {mode_normalized}"

        return f"❌ Invalid mode. Available: {', '.join(self.VALID_MODES)}"

    def set_fan_speed(self, speed: str) -> str:
        """Set fan speed with validation"""
        if not self.is_online:
            return f"❌ {self.name} is offline"

        if not self.state.get("power"):
            return f"❌ {self.name} is off. Turn it on first"

        speed_normalized = speed.lower().strip()

        if speed_normalized in self.VALID_FAN_SPEEDS:
            self.state["fan_speed"] = speed_normalized
            self.last_updated = datetime.now()
            return f"💨 {self.name} fan speed set to {speed_normalized}"

        return f"❌ Invalid fan speed. Available: {', '.join(self.VALID_FAN_SPEEDS)}"

    def get_status(self) -> str:
        """Get formatted AC status"""
        if not self.is_online:
            return f"{self.name} ({self.location}): OFFLINE 🔴"

        if self.state.get("power"):
            mode_emoji = self.MODE_EMOJIS.get(self.state.get("mode"), "❄️")
            return (f"{self.name} ({self.location}): ON 🟢 - "
                    f"{self.state.get('temperature')}°C 🌡️, "
                    f"{self.state.get('mode')} mode {mode_emoji}, "
                    f"{self.state.get('fan_speed')} fan 💨")

        return f"{self.name} ({self.location}): OFF 🔴"
