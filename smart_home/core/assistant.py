import logging
from typing import Dict, Any, Optional
from smart_home.config.app_config import my_config
from smart_home.devices.device_manager import DeviceManager
from smart_home.services.llm_service import LLMService
from smart_home.services.weather_service import WeatherService
from smart_home.services.news_service import NewsService
from smart_home.services.persian_service import PersianService

logger = logging.getLogger(__name__)


class SmartHomeAssistant:
    """
    Main Smart Home Assistant Class

    Features:
    - English + Persian language support
    - LLM-powered natural language processing
    - Device control with function calling
    - Weather and news information
    - Voice and text interfaces
    """

    def __init__(self):
        """Initialize the Smart Home Assistant"""
        logger.info("Initializing Smart Home Assistant...")

        # Validate configuration
        if not my_config.is_groq_configured():
            raise ValueError(
                "❌ GROQ_API_KEY not found in environment variables.\n"
                "Please:\n"
                "1. Copy .env.example to .env\n"
                "2. Add your Groq API key\n"
                "3. Get free key from: https://console.groq.com"
            )

        # Initialize core components
        self._initialize_components()

        # Success message
        self._show_initialization_summary()
        logger.info("Smart Home Assistant initialized successfully")

    def _initialize_components(self):
        """Initialize all components in correct order"""
        try:
            # Initialize device manager
            print("🔄 Loading devices...")
            self.device_manager = DeviceManager()

            # Initialize services
            print("🔄 Connecting to LLM service...")
            self.llm_service = LLMService()

            print("🔄 Setting up external services...")
            self.weather_service = WeatherService() if my_config.is_weather_configured() else None
            self.news_service = NewsService() if my_config.is_news_configured() else None

            print("🔄 Initializing Persian language support...")
            self.persian_service = PersianService(self.llm_service)

        except Exception as e:
            logger.error(f"Failed to initialize components: {e}")
            raise

    def _show_initialization_summary(self):
        """Show initialization summary"""
        print("\n" + "🏠" + "=" * 58 + "🏠")
        print("             SMART HOME ASSISTANT READY")
        print("🏠" + "=" * 58 + "🏠")

        # Device summary
        device_count = len(self.device_manager.get_all_devices())
        print(f"📱 Devices: {device_count} smart devices loaded")
        print(f"   💡 Lamps: {len(my_config.lamps)} locations")
        print(f"   ❄️  ACs: {len(my_config.acs)} locations")
        print(f"   📺 TVs: {len(my_config.tvs)} locations")

        # Language support
        print(f"🌍 Languages: English + Persian (automatic detection)")

        # Services status
        print(f"🤖 LLM: ✅ Groq LLaMA 3.3 70B")
        weather_status = "✅ Connected" if self.weather_service else "❌ Not configured"
        news_status = "✅ Connected" if self.news_service else "❌ Not configured"
        print(f"🌤️  Weather: {weather_status}")
        print(f"📰 News: {news_status}")
        print(f"🕒 Time: ✅ Available")

        # Persian support
        print(f"🇮🇷 Persian: ✅ Detection + Translation")

        # Quick setup tips
        if not self.weather_service:
            print(f"\n💡 Enable weather: Add WEATHER_API_KEY to .env")
            print(f"   Get free key: https://openweathermap.org/api")

        if not self.news_service:
            print(f"💡 Enable news: Add NEWS_API_KEY to .env")
            print(f"   Get free key: https://newsapi.org/")

        print("🏠" + "=" * 58 + "🏠")

    def process_command(self, user_input: str) -> str:
        """
        Process user command in any language

        Args:
            user_input: User command in English or Persian

        Returns:
            Response in the same language as input
        """
        try:
            if not user_input or not user_input.strip():
                return "❌ Please provide a command"

            logger.info(f"Processing command: '{user_input}'")

            # Check if input is Persian
            english_command, is_persian = self.persian_service.process_command(user_input)

            if is_persian:
                logger.info(f"Persian detected, translated to: '{english_command}'")

            # Process the English command
            english_response = self._process_english_command(english_command)

            # Translate response back to Persian if needed
            if is_persian:
                persian_response = self.persian_service.translate_to_persian(english_response)
                logger.info(f"Response translated to Persian: '{persian_response}'")
                return persian_response
            else:
                return english_response

        except Exception as e:
            logger.error(f"Error processing command: {e}")
            # Return error in appropriate language
            if self.persian_service.is_persian(user_input):
                return f"متأسفم، خطایی رخ داده: {str(e)}"
            else:
                return f"❌ Sorry, an error occurred: {str(e)}"

    def _process_english_command(self, command: str) -> str:
        """Process command in English using LLM"""
        try:
            # Use LLM service to process the command
            response = self.llm_service.process_command(
                command=command,
                device_manager=self.device_manager,
                weather_service=self.weather_service,
                news_service=self.news_service
            )

            return response

        except Exception as e:
            logger.error(f"Error processing English command: {e}")
            return f"❌ Error processing command: {str(e)}"

    def get_device_status(self, device_name: str = "all") -> str:
        """Get status of devices"""
        try:
            return self.device_manager.get_status(device_name)
        except Exception as e:
            logger.error(f"Error getting device status: {e}")
            return f"❌ Error getting device status: {str(e)}"

    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        try:
            device_count = len(self.device_manager.get_all_devices())

            # Count devices by type
            lamp_count = len(self.device_manager.get_devices_by_type("lamp"))
            ac_count = len(self.device_manager.get_devices_by_type("ac"))
            tv_count = len(self.device_manager.get_devices_by_type("tv"))

            # Count powered on devices
            powered_devices = 0
            for device in self.device_manager.get_all_devices().values():
                if device.state.get("power", False):
                    powered_devices += 1

            return {
                "total_devices": device_count,
                "powered_on": powered_devices,
                "device_types": {
                    "lamps": lamp_count,
                    "acs": ac_count,
                    "tvs": tv_count
                },
                "services": {
                    "llm": "✅ Connected",
                    "weather": "✅ Connected" if self.weather_service else "❌ Not configured",
                    "news": "✅ Connected" if self.news_service else "❌ Not configured",
                    "persian": "✅ Available",
                    "time": "✅ Available"
                },
                "languages": ["English", "Persian"],
                "configuration": {
                    "default_city": my_config.default_city,
                    "debug_mode": my_config.debug,
                    "log_level": my_config.log_level
                }
            }

        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {"error": str(e)}

    def test_services(self) -> Dict[str, str]:
        """Test all services and return results"""
        results = {}

        # Test LLM service
        try:
            test_response = self.llm_service.process_command(
                "test", self.device_manager, self.weather_service, self.news_service
            )
            results["llm"] = "✅ Working" if test_response else "❌ No response"
        except Exception as e:
            results["llm"] = f"❌ Error: {str(e)}"

        # Test weather service
        if self.weather_service:
            try:
                weather_response = self.weather_service.get_weather("Tehran")
                results["weather"] = "✅ Working" if not weather_response.startswith("❌") else weather_response
            except Exception as e:
                results["weather"] = f"❌ Error: {str(e)}"
        else:
            results["weather"] = "❌ Not configured"

        # Test news service
        if self.news_service:
            try:
                news_response = self.news_service.get_news("technology")
                results["news"] = "✅ Working" if not news_response.startswith("❌") else news_response
            except Exception as e:
                results["news"] = f"❌ Error: {str(e)}"
        else:
            results["news"] = "❌ Not configured"

        # Test Persian service
        try:
            persian_test = self.persian_service.is_persian("سلام")
            english_test = self.persian_service.is_persian("hello")
            results["persian"] = "✅ Working" if persian_test and not english_test else "❌ Detection issue"
        except Exception as e:
            results["persian"] = f"❌ Error: {str(e)}"

        # Test device manager
        try:
            device_status = self.device_manager.get_status()
            results["devices"] = "✅ Working" if device_status else "❌ No devices"
        except Exception as e:
            results["devices"] = f"❌ Error: {str(e)}"

        return results

    def get_example_commands(self) -> Dict[str, list]:
        """Get example commands for demonstration"""
        return {
            "english": [
                "Turn on the kitchen lamp",
                "Set the AC to 22 degrees",
                "What's the weather in Tehran?",
                "Get technology news",
                "Show device status",
                "Turn off all devices"
            ],
            "persian": [
                "چراغ آشپزخانه را روشن کن",
                "کولر را روی ۲۲ درجه تنظیم کن",
                "هوای تهران چطوره؟",
                "خبرهای فناوری بده",
                "وضعیت دستگاه‌ها را نشان بده",
                "همه دستگاه‌ها را خاموش کن"
            ]
        }

    def shutdown(self):
        """Gracefully shutdown the assistant"""
        try:
            logger.info("Shutting down Smart Home Assistant...")

            # Turn off all devices
            self.device_manager.control_device("all_devices", "off")

            print("👋 Smart Home Assistant shutdown complete")

        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

    def __str__(self) -> str:
        """String representation of the assistant"""
        device_count = len(self.device_manager.get_all_devices())
        return f"SmartHomeAssistant({device_count} devices, multilingual, LLM-powered)"

    def __repr__(self) -> str:
        """Technical representation of the assistant"""
        return (f"SmartHomeAssistant("
                f"devices={len(self.device_manager.get_all_devices())}, "
                f"weather={'✅' if self.weather_service else '❌'}, "
                f"news={'✅' if self.news_service else '❌'}, "
                f"persian=✅)")
