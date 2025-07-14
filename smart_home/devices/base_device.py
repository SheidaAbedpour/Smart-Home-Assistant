from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any


class SmartHomeDevice(ABC):
    """Abstract base class for all smart home devices"""

    def __init__(self, name: str, location: str, device_type: str, initial_state: Dict[str, Any] = None):
        self.name = name
        self.location = location
        self.device_type = device_type
        self.device_id = f"{location.lower().replace(' ', '_')}_{device_type}"
        self.state = initial_state or {"power": False}
        self.last_updated = datetime.now()
        self.is_online = True

    def turn_on(self) -> str:
        """Turn device on"""
        if not self.is_online:
            return f"❌ {self.name} is offline"

        self.state["power"] = True
        self.last_updated = datetime.now()
        return f"✅ {self.name} turned on"

    def turn_off(self) -> str:
        """Turn device off"""
        if not self.is_online:
            return f"❌ {self.name} is offline"

        self.state["power"] = False
        self.last_updated = datetime.now()
        return f"🔌 {self.name} turned off"

    def toggle(self) -> str:
        """Toggle device power state"""
        return self.turn_off() if self.state.get("power") else self.turn_on()

    @abstractmethod
    def get_status(self) -> str:
        """Get device status - must be implemented by subclasses"""
        pass

    def __str__(self) -> str:
        return f"{self.name} ({self.device_type}) - {self.location}"
