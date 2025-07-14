import logging
from typing import Dict, List, Optional
from smart_home.config.app_config import my_config
from smart_home.devices.lamp import SmartLamp
from smart_home.devices.air_conditioner import SmartAirConditioner
from smart_home.devices.television import SmartTelevision

logger = logging.getLogger(__name__)


class DeviceManager:
    """Manages all smart home devices"""

    def __init__(self):
        """Initialize device manager with devices from config"""
        self.devices: Dict[str, object] = {}
        self._create_devices()
        logger.info(f"Created {len(self.devices)} devices")

    def _create_devices(self):
        """Create all devices from configuration"""
        # Create lamps
        for location in my_config.lamps:
            device_id = f"{location.lower().replace(' ', '_')}_lamp"
            self.devices[device_id] = SmartLamp(location)

        # Create ACs
        for location in my_config.acs:
            device_id = f"{location.lower().replace(' ', '_')}_ac"
            self.devices[device_id] = SmartAirConditioner(location)

        # Create TVs
        for location in my_config.tvs:
            device_id = f"{location.lower().replace(' ', '_')}_tv"
            self.devices[device_id] = SmartTelevision(location)

    def get_device(self, device_id: str) -> Optional[object]:
        """Get device by ID"""
        return self.devices.get(device_id)

    def get_devices_by_type(self, device_type: str) -> List[object]:
        """Get all devices of specific type"""
        return [device for device_id, device in self.devices.items()
                if device_type in device_id]

    def get_all_devices(self) -> Dict[str, object]:
        """Get all devices"""
        return self.devices.copy()

    def control_device(self, device_type: str, action: str, location: str = None, value: str = None) -> str:
        """Control devices based on type and action"""
        try:
            # Handle special device types
            if device_type == "all_lamps":
                return self._control_all_lamps(action, value)
            elif device_type == "all_devices":
                return self._control_all_devices(action)

            # Handle specific device
            if not location:
                return "❌ Please specify the location for the device"

            device = self._get_device_by_pattern(device_type, location)
            if not device:
                return f"❌ Device not found: {device_type} in {location}"

            return self._execute_device_action(device, action, value)

        except Exception as e:
            logger.error(f"Error controlling device: {e}")
            return f"❌ Error controlling device: {str(e)}"

    def _get_device_by_pattern(self, device_type: str, location: str):
        """Get device by type and location pattern"""
        device_id = f"{location.lower().replace(' ', '_')}_{device_type}"
        return self.devices.get(device_id)

    def _control_all_lamps(self, action: str, value: str = None) -> str:
        """Control all lamps"""
        lamp_devices = self.get_devices_by_type("lamp")
        if not lamp_devices:
            return "❌ No lamps found"

        results = []
        for device in lamp_devices:
            result = self._execute_device_action(device, action, value)
            if not result.startswith("❌"):
                results.append(f"  • {result}")

        return f"💡 All lamps:\n" + "\n".join(results) if results else "❌ No lamps could be controlled"

    def _control_all_devices(self, action: str) -> str:
        """Control all devices (only supports off)"""
        if action != "off":
            return "❌ Only 'off' action is supported for all devices"

        results = []
        for device in self.devices.values():
            result = device.turn_off()
            if not result.startswith("❌"):
                results.append(f"  • {result}")

        return f"🔌 All devices turned off:\n" + "\n".join(results)

    def _execute_device_action(self, device, action: str, value: str = None) -> str:
        """Execute action on a specific device"""
        try:
            # Basic actions
            if action == "on":
                return device.turn_on()
            elif action == "off":
                return device.turn_off()
            elif action == "toggle":
                return device.toggle()

            # Lamp-specific actions
            elif action == "brightness" and hasattr(device, 'set_brightness'):
                if value:
                    return device.set_brightness(int(value))
                return "❌ Please specify brightness level (0-100)"

            elif action == "color" and hasattr(device, 'set_color'):
                if value:
                    return device.set_color(value)
                return "❌ Please specify a color"

            # AC-specific actions
            elif action == "temperature" and hasattr(device, 'set_temperature'):
                if value:
                    return device.set_temperature(int(value))
                return "❌ Please specify temperature (16-30°C)"

            elif action == "mode" and hasattr(device, 'set_mode'):
                if value:
                    return device.set_mode(value)
                return "❌ Please specify mode"

            elif action == "fan_speed" and hasattr(device, 'set_fan_speed'):
                if value:
                    return device.set_fan_speed(value)
                return "❌ Please specify fan speed"

            # TV-specific actions
            elif action == "channel" and hasattr(device, 'set_channel'):
                if value:
                    return device.set_channel(int(value))
                return "❌ Please specify channel number"

            elif action == "volume" and hasattr(device, 'set_volume'):
                if value:
                    return device.set_volume(int(value))
                return "❌ Please specify volume level"

            elif action == "input" and hasattr(device, 'set_input'):
                if value:
                    return device.set_input(value)
                return "❌ Please specify input"

            else:
                return f"❌ Action '{action}' not supported for {device.device_type}"

        except (ValueError, TypeError):
            return f"❌ Invalid value '{value}' for action '{action}'"
        except Exception as e:
            return f"❌ Error executing {action}: {str(e)}"

    def get_status(self, device_name: str = "all") -> str:
        """Get device status"""
        try:
            if device_name == "all":
                status_lines = ["📊 Smart Home Status:"]

                # Group by device type
                lamp_devices = self.get_devices_by_type("lamp")
                ac_devices = self.get_devices_by_type("ac")
                tv_devices = self.get_devices_by_type("tv")

                if lamp_devices:
                    status_lines.append("\n💡 Lamps:")
                    for device in lamp_devices:
                        status_lines.append(f"  • {device.get_status()}")

                if ac_devices:
                    status_lines.append("\n❄️ Air Conditioners:")
                    for device in ac_devices:
                        status_lines.append(f"  • {device.get_status()}")

                if tv_devices:
                    status_lines.append("\n📺 Televisions:")
                    for device in tv_devices:
                        status_lines.append(f"  • {device.get_status()}")

                return "\n".join(status_lines)
            else:
                # Find specific device
                for device_id, device in self.devices.items():
                    if device_name.lower() in device_id or device_name.lower() in device.name.lower():
                        return f"📊 {device.get_status()}"

                return f"❌ Device '{device_name}' not found"

        except Exception as e:
            logger.error(f"Error getting device status: {e}")
            return f"❌ Error getting device status: {str(e)}"
