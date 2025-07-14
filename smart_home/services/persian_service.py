import re
import logging
from typing import Tuple
from smart_home.services.llm_service import LLMService

logger = logging.getLogger(__name__)


class PersianService:
    """Persian language detection and translation service"""

    def __init__(self, llm_service: LLMService):
        """Initialize Persian service"""
        self.llm_service = llm_service

        # Persian character ranges for detection
        self.persian_ranges = [
            (0x0600, 0x06FF),  # Arabic/Persian script
            (0xFB50, 0xFDFF),  # Arabic Presentation Forms-A
            (0xFE70, 0xFEFF),  # Arabic Presentation Forms-B
        ]

        # Common Persian words for detection
        self.persian_words = [
            "روشن", "خاموش", "چراغ", "تلویزیون", "کولر", "هوا", "خبر", "وقت", "ساعت",
            "دما", "درجه", "کانال", "صدا", "رنگ", "صبح", "شب", "آشپزخانه", "حمام",
            "اتاق", "پذیرایی", "سلام", "چطور", "چی", "چه", "کن", "بده", "همه", "تمام"
        ]

        # Quick translation patterns for common commands
        self.quick_patterns = {
            # Complete command patterns
            "چراغ آشپزخانه را روشن کن": "turn on the kitchen lamp",
            "چراغ حمام را روشن کن": "turn on the bathroom lamp",
            "چراغ اتاق یک را روشن کن": "turn on the room 1 lamp",
            "چراغ اتاق دو را روشن کن": "turn on the room 2 lamp",
            "چراغ آشپزخانه را خاموش کن": "turn off the kitchen lamp",
            "چراغ حمام را خاموش کن": "turn off the bathroom lamp",
            "همه چراغ‌ها را روشن کن": "turn on all lamps",
            "همه چراغ‌ها را خاموش کن": "turn off all lamps",

            "کولر را روشن کن": "turn on the AC",
            "کولر اتاق یک را روشن کن": "turn on the room 1 AC",
            "کولر آشپزخانه را روشن کن": "turn on the kitchen AC",
            "کولر را خاموش کن": "turn off the AC",

            "تلویزیون را روشن کن": "turn on the TV",
            "تلویزیون را خاموش کن": "turn off the TV",
            "تی وی را روشن کن": "turn on the TV",
            "تی وی را خاموش کن": "turn off the TV",

            "همه دستگاه‌ها را خاموش کن": "turn off all devices",
            "تمام دستگاه‌ها را خاموش کن": "turn off all devices",

            "وضعیت دستگاه‌ها چیه": "what is the status of all devices",
            "وضعیت دستگاه‌ها را نشان بده": "show device status",
            "دستگاه‌ها چطورن": "how are the devices",

            "هوا چطوره": "what's the weather",
            "هوای تهران چطوره": "what's the weather in Tehran",
            "آب و هوا چطوره": "what's the weather",
            "آب و هوای تهران": "weather in Tehran",

            "ساعت چنده": "what time is it",
            "وقت چیه": "what time is it",
            "زمان چقدره": "what time is it",
            "الان ساعت چنده": "what time is it now",
        }

        # Persian to English digit mapping
        self.persian_digits = "۰۱۲۳۴۵۶۷۸۹"
        self.english_digits = "0123456789"

        logger.info("Persian service initialized")

    def is_persian(self, text: str) -> bool:
        """Detect if text contains Persian"""
        if not text or not text.strip():
            return False

        # Check for Persian characters
        persian_char_count = 0
        total_chars = 0

        for char in text:
            if char.isalpha():
                total_chars += 1
                char_code = ord(char)
                for start, end in self.persian_ranges:
                    if start <= char_code <= end:
                        persian_char_count += 1
                        break

        # If more than 30% Persian characters, consider it Persian
        if total_chars > 0 and (persian_char_count / total_chars) > 0.3:
            return True

        # Check for Persian indicator words
        text_lower = text.lower()
        for word in self.persian_words:
            if word in text_lower:
                return True

        return False

    def translate_to_english(self, persian_text: str) -> str:
        """Translate Persian text to English"""
        if not self.is_persian(persian_text):
            return persian_text

        # Convert Persian digits to English
        translated = persian_text
        for i, persian_digit in enumerate(self.persian_digits):
            translated = translated.replace(persian_digit, self.english_digits[i])

        # Check for quick pattern matches
        text_lower = translated.lower().strip()
        for persian_pattern, english_translation in self.quick_patterns.items():
            if persian_pattern in text_lower:
                logger.info(f"Quick pattern match: '{persian_pattern}' -> '{english_translation}'")
                return english_translation

        # Handle temperature patterns
        temp_patterns = [
            (r'کولر را روی (\d+) درجه تنظیم کن', r'set AC to \1 degrees'),
            (r'کولر (.+) را روی (\d+) درجه تنظیم کن', r'set \1 AC to \2 degrees'),
            (r'دما را روی (\d+) تنظیم کن', r'set temperature to \1'),
        ]

        for persian_pattern, english_pattern in temp_patterns:
            match = re.search(persian_pattern, text_lower)
            if match:
                result = re.sub(persian_pattern, english_pattern, text_lower)
                result = result.replace('اتاق یک', 'room 1').replace('آشپزخانه', 'kitchen')
                logger.info(f"Temperature pattern: '{persian_text}' -> '{result}'")
                return result

        # Handle brightness patterns
        brightness_patterns = [
            (r'چراغ را روی (\d+) درصد روشنی تنظیم کن', r'set lamp to \1% brightness'),
            (r'چراغ (.+) را روی (\d+) درصد تنظیم کن', r'set \1 lamp to \2% brightness'),
            (r'روشنی چراغ را (\d+) درصد کن', r'set lamp brightness to \1%'),
        ]

        for persian_pattern, english_pattern in brightness_patterns:
            match = re.search(persian_pattern, text_lower)
            if match:
                result = re.sub(persian_pattern, english_pattern, text_lower)
                result = result.replace('آشپزخانه', 'kitchen').replace('حمام', 'bathroom')
                logger.info(f"Brightness pattern: '{persian_text}' -> '{result}'")
                return result

        # Use LLM for complex translations
        logger.info(f"Using LLM translation for: '{persian_text}'")
        return self.llm_service.translate_text(persian_text, "english")

    def translate_to_persian(self, english_text: str) -> str:
        """Translate English response to Persian"""
        return self.llm_service.translate_text(english_text, "persian")

    def process_command(self, command: str) -> Tuple[str, bool]:
        """
        Process command and return (translated_command, is_persian)

        Returns:
            Tuple of (processed_command, was_persian)
        """
        if self.is_persian(command):
            english_command = self.translate_to_english(command)
            return english_command, True
        else:
            return command, False
