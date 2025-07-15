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
        self.conversation_history = []

        logger.info("LLM service initialized")

    def process_command(self, command: str, device_manager, weather_service=None, news_service=None) -> str:
        """Process user command using LLM with function calling"""
        try:
            logger.info(f"🧠 LLM processing command: '{command}'")

            # Get available functions
            functions = self._get_function_definitions()

            # Create system prompt
            system_prompt = self._create_system_prompt()
            messages = [{"role": "system", "content": system_prompt}]

            # Add last 6 messages (3 exchanges) for context
            for entry in self.conversation_history[-6:]:
                messages.append({"role": "user", "content": entry["user"]})
                messages.append({"role": "assistant", "content": entry["assistant"]})

            # Add current user message
            messages.append({"role": "user", "content": command})

            logger.info(f"🔧 Calling Groq API with {len(messages)} messages")

            # Send to LLM
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                functions=functions,
                function_call="auto",
                temperature=0.1,
                max_tokens=2000,
                timeout=30
            )

            message = response.choices[0].message
            logger.info(f"📨 LLM response received, has function call: {bool(message.function_call)}")

            # Check if response contains function call text (Groq bug workaround)
            if message.content and '<function=' in message.content:
                logger.info("🔧 Detected function call in text format, parsing...")
                final_response = self._parse_and_execute_function_from_text(
                    message.content, device_manager, weather_service, news_service
                )
                logger.info(f"🎯 Parsed function response: '{final_response}'")
            elif message.function_call:
                # Execute function (normal case)
                function_name = message.function_call.name
                function_args = json.loads(message.function_call.arguments)

                logger.info(f"🔧 Executing function: {function_name} with args: {function_args}")

                # Execute the function
                function_result = self._execute_function(
                    function_name, function_args, device_manager, weather_service, news_service
                )

                logger.info(f"⚙️ Function result: {function_result}")

                # Generate natural response with conversation history
                follow_up = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages + [
                        {"role": "assistant", "content": "", "function_call": message.function_call},
                        {"role": "function", "name": function_name, "content": function_result}
                    ],
                    temperature=0.3,
                    max_tokens=2000,
                    timeout=30
                )

                final_response = follow_up.choices[0].message.content
                logger.info(f"🎯 Final LLM response: '{final_response}' (length: {len(final_response)})")
            else:
                final_response = message.content
                logger.info(f"💬 Direct LLM response: '{final_response}' (length: {len(final_response)})")

                # Additional check for function calls in content
                if final_response and '<function=' in final_response:
                    logger.info("🔧 Found function call in direct response, parsing...")
                    final_response = self._parse_and_execute_function_from_text(
                        final_response, device_manager, weather_service, news_service
                    )

            # Validate response
            if not final_response:
                logger.warning("⚠️ LLM returned empty response")
                final_response = "I processed your request, but didn't generate a response. Please try again."
            elif len(final_response.strip()) == 0:
                logger.warning("⚠️ LLM returned whitespace-only response")
                final_response = "I received your command but my response was empty. Please try again."

            # Save conversation to history
            self.conversation_history.append({
                "user": command,
                "assistant": final_response
            })

            # Keep only last 20 conversations
            if len(self.conversation_history) > 20:
                self.conversation_history = self.conversation_history[-20:]

            logger.info(f"✅ Returning response of length {len(final_response)}")
            return final_response

        except Exception as e:
            logger.error(f"❌ Error processing command: {e}")
            import traceback
            traceback.print_exc()
            return f"❌ Error processing command: {str(e)}"

    def _parse_and_execute_function_from_text(self, text_response: str, device_manager, weather_service,
                                              news_service) -> str:
        """Parse function calls from text and execute them (Groq workaround)"""
        try:
            import re

            # Extract function calls from text like <function=control_device{"device_type": "lamp", "action": "on", "location": "room 1"}</function>
            function_pattern = r'<function=([^{]+)(\{[^}]+\})</function>'
            matches = re.findall(function_pattern, text_response)

            if not matches:
                logger.warning("No function calls found in text")
                return "I understood your request but couldn't execute it properly."

            # Process the first function call
            function_name, function_args_str = matches[0]
            logger.info(f"🔧 Parsing function: {function_name} with args: {function_args_str}")

            # Clean up the function name
            function_name = function_name.strip()

            # Parse the JSON arguments
            try:
                function_args = json.loads(function_args_str)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse function arguments: {e}")
                return "I understood your request but couldn't parse the parameters properly."

            # Execute the function
            function_result = self._execute_function(
                function_name, function_args, device_manager, weather_service, news_service
            )

            logger.info(f"⚙️ Function execution result: {function_result}")

            # Return a natural response based on the function result
            if function_name == "control_device":
                if "turned on" in function_result.lower():
                    return f"✅ {function_result}"
                elif "turned off" in function_result.lower():
                    return f"🔌 {function_result}"
                elif "set to" in function_result.lower():
                    return f"⚙️ {function_result}"
                else:
                    return function_result
            else:
                return function_result

        except Exception as e:
            logger.error(f"Error parsing function from text: {e}")
            return f"I understood your request but encountered an error: {str(e)}"

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

IMPORTANT INSTRUCTIONS:
- ALWAYS provide a clear, complete response
- Be specific about what action was taken
- Use emojis to make responses friendly
- If controlling devices, confirm the action taken
- Keep responses conversational but informative
- NEVER give partial or incomplete responses

CONVERSATION AWARENESS:
- You can see the conversation history above
- If the user's current message seems incomplete or related to previous messages, use context to understand what they want
- For example:
  * If you asked "Which city?" and user says "Tehran", get weather for Tehran
  * If you asked "Which room?" and user says "kitchen", control the kitchen device
  * If user says just "22" or "22 degrees" after temperature question, set temperature to 22
  * If user says just a city name after weather question, get weather for that city
  * If user says just a room name after device question, control device in that room
  * If user says "yes" check your previous conversation and check what user was referring to

- Look at the conversation history to understand incomplete responses
- If user gives incomplete info and there's no context, ask for clarification naturally
- If user asks for news show it completely 

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
- ALWAYS complete your thoughts and responses

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
            logger.info(f"🔧 Executing function: {function_name}")

            if function_name == "control_device":
                result = device_manager.control_device(**args)
                logger.info(f"🏠 Device control result: {result}")
                return result
            elif function_name == "get_weather":
                city = args.get("city", my_config.default_city)
                result = weather_service.get_weather(city) if weather_service else "❌ Weather service not available"
                logger.info(f"🌤️ Weather result: {result}")
                return result
            elif function_name == "get_news":
                category = args.get("category", "technology")
                result = news_service.get_news(category) if news_service else "❌ News service not available"
                logger.info(f"📰 News result: {result}")
                return result
            elif function_name == "get_time":
                from smart_home.services.time_service import TimeService
                result = TimeService.get_current_time()
                logger.info(f"🕒 Time result: {result}")
                return result
            elif function_name == "get_device_status":
                device = args.get("device", "all")
                result = device_manager.get_status(device)
                logger.info(f"📊 Status result: {result}")
                return result
            else:
                error_msg = f"❌ Unknown function: {function_name}"
                logger.error(error_msg)
                return error_msg

        except Exception as e:
            error_msg = f"❌ Error executing {function_name}: {str(e)}"
            logger.error(error_msg)
            return error_msg

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
                temperature=0.3,
                max_tokens=2000,
                timeout=15
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"Translation error: {e}")
            return text
