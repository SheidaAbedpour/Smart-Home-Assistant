import json
import logging
from typing import Dict, List, Any
from groq import Groq
from smart_home.config.app_config import my_config

logger = logging.getLogger(__name__)


class LLMService:
    """LLM service for processing natural language commands"""

    def __init__(self):
        """Initialize LLM service"""
        if not my_config.is_groq_configured():
            raise ValueError("Groq API key not configured")

        self.client = Groq(api_key=my_config.groq_api_key)
        self.model = "llama-3.3-70b-versatile"

        logger.info("LLM service initialized")

    def process_command(self, command: str, device_manager, weather_service=None, news_service=None) -> str:
        """Process user command using LLM with function calling"""
        try:
            # Get available functions
            functions = self._get_function_definitions()

            # Create system prompt
            system_prompt = self._create_system_prompt()

            # Send to LLM
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": command}
                ],
                functions=functions,
                function_call="auto",
                temperature=0.1,
                max_tokens=4000
            )

            message = response.choices[0].message

            if message.function_call:
                # Execute function
                function_name = message.function_call.name
                function_args = json.loads(message.function_call.arguments)

                logger.info(f"Executing function: {function_name} with args: {function_args}")

                # Execute the function
                function_result = self._execute_function(
                    function_name, function_args, device_manager, weather_service, news_service
                )

                # Generate natural response
                follow_up = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": command},
                        {"role": "assistant", "content": "", "function_call": message.function_call},
                        {"role": "function", "name": function_name, "content": function_result}
                    ],
                    temperature=0.3,
                    max_tokens=2000
                )

                return follow_up.choices[0].message.content
            else:
                return message.content

        except Exception as e:
            logger.error(f"Error processing command: {e}")
            return f"❌ Error processing command: {str(e)}"

    def _create_system_prompt(self) -> str:
        """Create system prompt for the assistant"""
        return f"""You are a helpful smart home assistant that controls devices and provides information.

AVAILABLE DEVICES:
💡 Lamps in: {', '.join(my_config.lamps)}
❄️ ACs in: {', '.join(my_config.acs)}  
📺 TVs in: {', '.join(my_config.tvs)}

DEVICE CAPABILITIES:
- Lamps: turn on/off, set brightness (0-100%), change colors (white, red, blue, green, yellow, purple, orange)
- ACs: turn on/off, set temperature (16-30°C), change modes (cool, heat, fan, auto, dry), set fan speed (low, medium, high, auto)
- TVs: turn on/off, change channels (1-999), set volume (0-100%), change inputs (hdmi1, hdmi2, hdmi3, usb, cable, antenna, netflix, youtube)

AVAILABLE FUNCTIONS:
- control_device: Control any smart home device
- get_weather: Get current weather information
- get_news: Get latest news headlines
- get_time: Get current date and time
- get_device_status: Check device status

RESPONSE STYLE:
- Be conversational and helpful
- Use appropriate emojis
- Provide clear confirmations
- If user asks to adjust after weather, make smart suggestions

Always use the appropriate function for the user's request."""

    def _get_function_definitions(self) -> List[Dict]:
        """Get function definitions for LLM"""
        all_locations = list(set(my_config.lamps + my_config.acs + my_config.tvs + ["all"]))

        return [
            {
                "name": "control_device",
                "description": "Control smart home devices",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "device_type": {
                            "type": "string",
                            "enum": ["lamp", "ac", "tv", "all_lamps", "all_devices"]
                        },
                        "location": {
                            "type": "string",
                            "enum": [loc.lower() for loc in all_locations]
                        },
                        "action": {
                            "type": "string",
                            "enum": ["on", "off", "toggle", "brightness", "color", "temperature", "mode", "fan_speed",
                                     "channel", "volume", "input"]
                        },
                        "value": {"type": "string"}
                    },
                    "required": ["device_type", "action"]
                }
            },
            {
                "name": "get_weather",
                "description": "Get current weather information",
                "parameters": {
                    "type": "object",
                    "properties": {"city": {"type": "string"}}
                }
            },
            {
                "name": "get_news",
                "description": "Get latest news headlines",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "category": {
                            "type": "string",
                            "enum": ["technology", "business", "sports", "health", "science", "general",
                                     "entertainment"]
                        }
                    }
                }
            },
            {
                "name": "get_time",
                "description": "Get current date and time",
                "parameters": {"type": "object", "properties": {}}
            },
            {
                "name": "get_device_status",
                "description": "Get device status",
                "parameters": {
                    "type": "object",
                    "properties": {"device": {"type": "string"}}
                }
            }
        ]

    def _execute_function(self, function_name: str, args: Dict, device_manager, weather_service, news_service) -> str:
        """Execute the specified function"""
        try:
            if function_name == "control_device":
                return device_manager.control_device(**args)
            elif function_name == "get_weather":
                city = args.get("city", my_config.default_city)
                return weather_service.get_weather(city) if weather_service else "❌ Weather service not available"
            elif function_name == "get_news":
                category = args.get("category", "technology")
                return news_service.get_news(category) if news_service else "❌ News service not available"
            elif function_name == "get_time":
                from smart_home.services.time_service import TimeService
                return TimeService.get_current_time()
            elif function_name == "get_device_status":
                device = args.get("device", "all")
                return device_manager.get_status(device)
            else:
                return f"❌ Unknown function: {function_name}"

        except Exception as e:
            logger.error(f"Error executing {function_name}: {e}")
            return f"❌ Error executing {function_name}: {str(e)}"

    def translate_text(self, text: str, target_language: str) -> str:
        """Translate text using LLM"""
        try:
            if target_language.lower() == "persian" or target_language.lower() == "fa":
                system_prompt = """You are a translator. Translate the English text to natural, conversational Persian.

Examples:
"Kitchen lamp turned on" → "چراغ آشپزخانه روشن شد"
"AC temperature set to 22 degrees" → "دمای کولر روی ۲۲ درجه تنظیم شد"
"Current weather in Tehran is sunny, 25°C" → "هوای فعلی تهران آفتابی است، ۲۵ درجه سانتی گراد"

IMPORTANT: Output ONLY the Persian translation."""
            else:
                system_prompt = """You are a translator. Translate the Persian text to natural English.

Examples:
"چراغ آشپزخانه را روشن کن" → "turn on the kitchen lamp"
"کولر را روی ۲۲ درجه تنظیم کن" → "set AC to 22 degrees"
"هوای تهران چطوره؟" → "what's the weather in Tehran"

IMPORTANT: Output ONLY the English translation."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ],
                temperature=0.1,
                max_tokens=300
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"Translation error: {e}")
            return text
