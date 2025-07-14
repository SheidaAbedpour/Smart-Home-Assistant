import numpy as np
import sounddevice as sd
import threading
import queue
import time
import logging
import re
import unicodedata
from typing import Optional, Callable
import whisper
from gtts import gTTS
import pygame
import tempfile
import os
from smart_home.core.assistant import SmartHomeAssistant
from smart_home.config.app_config import my_config

logger = logging.getLogger(__name__)


class VoiceInterface:
    """
    voice interface with comprehensive text cleaning for natural speech

    Features:
    - Wake word detection
    - Speech-to-text with Whisper
    - Advanced text cleaning for natural TTS
    - Complete emoji removal using Unicode
    - Smart number and measurement conversion
    - Multilingual support
    - Audio feedback prevention
    """

    def __init__(self, assistant: SmartHomeAssistant):
        """Initialize enhanced voice interface"""
        self.assistant = assistant
        self.wake_words = ["hey assistant", "hey", "assistant"]

        # Audio settings
        self.sample_rate = 16000
        self.chunk_size = 1024

        # State management
        self.is_listening = False
        self.is_recording_command = False
        self.listening_paused = False
        self.is_speaking = False

        # Audio processing
        self.audio_queue = queue.Queue()
        self.command_queue = queue.Queue()
        self.audio_buffer = []

        # Voice components
        self.whisper_model = None
        self.noise_level = 0.0
        self.vad_threshold = 0.003

        # Threading
        self.command_lock = threading.Lock()

        # Initialize enhanced text cleaning
        self._init_enhanced_cleaning()

        # Initialize components
        self._initialize_voice_components()

    def _init_enhanced_cleaning(self):
        """Initialize enhanced text cleaning system"""
        # Comprehensive number to word mapping
        self.ones = [
            "", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
            "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen",
            "seventeen", "eighteen", "nineteen"
        ]

        self.tens = [
            "", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"
        ]

        # Persian digits to English
        self.persian_to_english = str.maketrans('۰۱۲۳۴۵۶۷۸۹', '0123456789')

        # Device and location normalizations
        self.device_normalizations = {
            'AC': 'air conditioner', 'TV': 'television',
            'Room 1': 'room one', 'Room 2': 'room two', 'Room 3': 'room three',
            'Room1': 'room one', 'Room2': 'room two', 'Room3': 'room three',
            'Living Room': 'living room', 'Dining Room': 'dining room',
            'Kitchen': 'kitchen', 'Bathroom': 'bathroom', 'Bedroom': 'bedroom',
            'WiFi': 'Wi-Fi', 'USB': 'U S B', 'HDMI': 'H D M I'
        }

    def _initialize_voice_components(self):
        """Initialize voice recognition components"""
        try:
            print("🔄 Loading enhanced voice components...")

            # Initialize Whisper
            print("   📥 Loading Whisper model...")
            self.whisper_model = whisper.load_model("base")
            print("   ✅ Whisper model loaded")

            # Initialize pygame for TTS
            pygame.mixer.init()
            print("   ✅ TTS system ready")

            print("✅ Voice interface ready!")

        except Exception as e:
            logger.error(f"Error initializing voice components: {e}")
            raise Exception(f"Failed to initialize voice components: {e}")

    def run(self):
        """Start the enhanced voice interface"""
        if not self.whisper_model:
            print("❌ Voice components not ready")
            return

        self._show_voice_welcome()

        self.is_listening = True

        try:
            # Start audio stream
            self._start_audio_stream()

            # Start processing thread
            processor_thread = threading.Thread(target=self._audio_processor_loop, daemon=True)
            processor_thread.start()

            # Initial greeting
            self._speak("Voice assistant ready. Say hey assistant to give commands.")

            print("✅ Voice interface active!")
            print("👂 Listening for wake words...")
            print("💡 Say: 'Hey assistant' then give your command")
            print("💡 Try: 'Hey assistant, what time is it?'")
            print("💡 Or: 'Hey assistant, what's the weather?'")
            print("💡 Persian: 'Hey assistant, چراغ آشپزخانه را روشن کن'")
            print("💡 Press Ctrl+C to stop")
            print("-" * 60)

            # Main loop
            while self.is_listening:
                time.sleep(0.1)

        except KeyboardInterrupt:
            print("\n🔇 Stopping voice interface...")
            self.stop_listening()
        except Exception as e:
            logger.error(f"Voice interface error: {e}")
            print(f"❌ Voice interface error: {e}")

    def _show_voice_welcome(self):
        """Show enhanced voice interface welcome"""
        print("\n" + "🎤" + "=" * 58 + "🎤")
        print("     SMART HOME ASSISTANT - ENHANCED VOICE CONTROL")
        print("🎤" + "=" * 58 + "🎤")
        print("🌍 Multilingual Support: English + Persian")
        print("👂 Wake Words: " + ", ".join(f"'{w}'" for w in self.wake_words))
        print("🗣️  Speech-to-Text: OpenAI Whisper")
        print("🔊 Text-to-Speech: Google TTS + Enhanced Cleaning")
        print("🧹 Features: Complete emoji removal, smart number conversion")
        print("🎤" + "=" * 58 + "🎤")

    def _start_audio_stream(self):
        """Start audio input stream"""
        try:
            def audio_callback(indata, frames, time_info, status):
                if not self.is_listening:
                    return

                audio_data = indata[:, 0] if len(indata.shape) > 1 else indata.flatten()

                # Don't process audio when speaking (prevents feedback)
                if self.is_speaking:
                    return

                # Always add to command queue if recording
                if self.is_recording_command:
                    self.command_queue.put(audio_data.copy())

                # Only process for wake words when not paused
                if not self.listening_paused:
                    max_vol = np.max(np.abs(audio_data))
                    if max_vol > 0.002:
                        self.audio_queue.put(audio_data.copy())

            self.audio_stream = sd.InputStream(
                callback=audio_callback,
                samplerate=self.sample_rate,
                channels=1,
                dtype=np.float32,
                blocksize=self.chunk_size
            )

            self.audio_stream.start()
            logger.info("Audio stream started")

        except Exception as e:
            logger.error(f"Audio stream error: {e}")
            raise Exception(f"Failed to start audio stream: {e}")

    def _audio_processor_loop(self):
        """Main audio processing loop"""
        while self.is_listening:
            try:
                # Get audio chunk with timeout
                audio_chunk = self.audio_queue.get(timeout=1.0)

                # Skip processing if speaking
                if self.is_speaking:
                    continue

                # Add to buffer
                self.audio_buffer.extend(audio_chunk)

                # Keep last 4 seconds
                max_samples = self.sample_rate * 4
                if len(self.audio_buffer) > max_samples:
                    self.audio_buffer = self.audio_buffer[-max_samples:]

                # Check for voice activity
                if self._detect_voice_activity(audio_chunk):
                    if len(self.audio_buffer) >= self.sample_rate * 2:
                        self._check_for_wake_word()

            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Audio processing error: {e}")

    def _detect_voice_activity(self, audio_chunk: np.ndarray) -> bool:
        """Voice activity detection"""
        try:
            # Don't detect voice when speaking
            if self.is_speaking:
                return False

            # Calculate RMS volume
            volume = np.sqrt(np.mean(audio_chunk ** 2))

            # Update noise level estimate
            if self.noise_level == 0.0:
                self.noise_level = volume
            else:
                self.noise_level = self.noise_level * 0.95 + volume * 0.05

            threshold = max(0.005, self.noise_level * 2)
            voice_detected = volume > threshold

            # DEBUGGING: Show more information
            if voice_detected:
                print(f"🎤 Voice detected! Vol: {volume:.4f}")

            return voice_detected

        except Exception as e:
            logger.error(f"VAD error: {e}")
            return False

    def _check_for_wake_word(self):
        """Check recent audio for wake words"""
        try:
            # Skip if already recording or speaking
            if self.is_recording_command or self.is_speaking:
                return

            # Get recent audio (last 3 seconds)
            recent_samples = min(self.sample_rate * 3, len(self.audio_buffer))
            if recent_samples < self.sample_rate:
                return

            recent_audio = np.array(self.audio_buffer[-recent_samples:], dtype=np.float32)

            # DEBUGGING: Check audio level
            audio_level = np.max(np.abs(recent_audio))
            print(f"\n🔍 Checking for wake word... Audio level: {audio_level:.4f}, Buffer size: {recent_samples}")

            # Recognize speech
            result = self.whisper_model.transcribe(recent_audio, language='en', fp16=False, temperature=0.0)
            text = result["text"].strip().lower()

            if not text:
                print("❌ No text recognized from audio")
                return

            print(f"👂 Heard: '{text}'")

            # wake word detection
            text_words = text.split()
            for wake_word in self.wake_words:
                wake_parts = wake_word.lower().split()

                # Check if all parts of wake word are in the text
                if all(part in text for part in wake_parts):
                    print(f"🎯 Wake word detected: '{wake_word}' in '{text}'")
                    self._handle_wake_word()
                    return

            print(f"❌ No wake word found in: '{text}'")

        except Exception as e:
            logger.error(f"Wake word detection error: {e}")
            print(f"❌ Wake word detection error: {e}")

    def _handle_wake_word(self):
        """Handle wake word detection"""
        with self.command_lock:
            if self.is_recording_command or self.is_speaking:
                return

            print("🎯 Wake word detected! Preparing to record...")
            self.is_recording_command = True

            # Clear command queue
            while not self.command_queue.empty():
                try:
                    self.command_queue.get_nowait()
                except queue.Empty:
                    break

        # Acknowledge and start recording
        self._pause_listening()
        self._speak("Yes?")

        # Wait for TTS to finish before resuming
        self._wait_for_speech_complete()
        self._resume_listening()

        # Start command recording in separate thread
        threading.Thread(target=self._record_command, daemon=True).start()

    def _record_command(self):
        """Record and process voice command"""
        print("🎙️ Recording command... (speak now)")

        try:
            command_audio = []
            start_time = time.time()
            last_voice_time = start_time

            # Give user time to start speaking
            time.sleep(0.5)

            while self.is_recording_command:
                try:
                    audio_chunk = self.command_queue.get(timeout=0.3)
                    command_audio.append(audio_chunk)

                    # Check for voice activity
                    if self._detect_voice_activity(audio_chunk):
                        last_voice_time = time.time()
                        print("🎤 Recording...", end="\r", flush=True)

                    # Check timeouts
                    elapsed = time.time() - start_time
                    silence_duration = time.time() - last_voice_time

                    # Stop recording if too much time or silence
                    if elapsed > 10 or (elapsed > 1 and silence_duration > 2.5):
                        print("\n⏹️ Command recording finished")
                        break

                except queue.Empty:
                    elapsed = time.time() - start_time
                    if elapsed > 8:
                        print("\n⏹️ Command recording timeout")
                        break

            # Process the recorded command
            if command_audio and len(command_audio) > 3:
                combined_audio = np.concatenate(command_audio)
                print("🔄 Processing command...")
                self._process_voice_command(combined_audio)
            else:
                print("⚠️ No command recorded")
                self._speak("I didn't hear a command.")

        except Exception as e:
            logger.error(f"Command recording error: {e}")
            self._speak("Sorry, I had trouble recording.")
        finally:
            with self.command_lock:
                self.is_recording_command = False
                # Wait for any TTS to complete before resuming
                self._wait_for_speech_complete()
                print("✅ Ready for next wake word...")

    def _process_voice_command(self, audio_data: np.ndarray):
        """Process recorded voice command"""
        try:
            # Recognize speech
            result = self.whisper_model.transcribe(
                audio_data,
                language='en',
                fp16=False,
                temperature=0.0
            )
            command = result["text"].strip()

            if command:
                print(f"📝 Command: '{command}'")

                # Send to assistant
                try:
                    response = self.assistant.process_command(command)
                    if response:
                        print(f"🤖 Original Response: {response}")

                        # Speech cleaning
                        is_persian = self.assistant.persian_service.is_persian(response)
                        clean_response = self._clean_for_speech(response, is_persian)

                        print(f"🧹 Cleaned for Speech: {clean_response}")
                        self._speak(clean_response, is_persian)
                    else:
                        self._speak("Done.")

                except Exception as e:
                    logger.error(f"Command execution error: {e}")
                    self._speak("Sorry, I had trouble with that command.")
            else:
                print("⚠️ Could not understand command")
                self._speak("I couldn't understand that. Please try again.")

        except Exception as e:
            logger.error(f"Command processing error: {e}")
            self._speak("Sorry, I had an error processing that.")

    def _clean_for_speech(self, text: str, is_persian: bool = False) -> str:
        """
        Enhanced comprehensive text cleaning for natural speech synthesis
        """
        try:
            if not text or not text.strip():
                return ""

            logger.debug(f"Cleaning text for speech: '{text}'")

            # Handle Persian text differently
            if is_persian:
                return self._clean_persian_text(text)

            cleaned = text

            # Step 1: Remove ALL emojis and symbols systematically
            cleaned = self._remove_all_emojis_and_symbols(cleaned)

            # Step 2: Handle Persian digits in mixed text
            cleaned = cleaned.translate(self.persian_to_english)

            # Step 3: Normalize spacing and punctuation
            cleaned = self._normalize_spacing_and_punctuation(cleaned)

            # Step 4: Convert time formats
            cleaned = self._convert_time_formats(cleaned)

            # Step 5: Convert temperature and measurements
            cleaned = self._convert_measurements(cleaned)

            # Step 6: Convert percentages
            cleaned = self._convert_percentages(cleaned)

            # Step 7: Convert decimal numbers
            cleaned = self._convert_decimal_numbers(cleaned)

            # Step 8: Convert whole numbers
            cleaned = self._convert_whole_numbers(cleaned)

            # Step 9: Expand abbreviations and device names
            cleaned = self._expand_abbreviations_and_devices(cleaned)

            # Step 10: Handle remaining special characters
            cleaned = self._handle_special_characters(cleaned)

            # Step 11: Final cleanup and validation
            cleaned = self._final_cleanup(cleaned)

            # Log the transformation if significant
            if len(cleaned) < len(text) * 0.8:  # If we removed > 20%
                logger.info(f"Text significantly cleaned: '{text}' → '{cleaned}'")

            return cleaned

        except Exception as e:
            logger.error(f"Error in enhanced text cleaning: {e}")
            # Fallback: basic cleaning
            return self._basic_fallback_cleaning(text)

    def _remove_all_emojis_and_symbols(self, text: str) -> str:
        """Remove ALL emojis and unwanted symbols using comprehensive Unicode ranges"""
        # Comprehensive emoji removal using Unicode blocks
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags (iOS)
            "\U0001F900-\U0001F9FF"  # supplemental symbols
            "\U00002600-\U000026FF"  # miscellaneous symbols
            "\U00002700-\U000027BF"  # dingbats
            "\U0000FE00-\U0000FE0F"  # variation selectors
            "\U0001F200-\U0001F2FF"  # enclosed characters
            "\U00003030"  # wavy dash
            "\U0001F004"  # mahjong tile
            "\U0001F0CF"  # playing card
            "]+",
            flags=re.UNICODE
        )

        text = emoji_pattern.sub(' ', text)

        # Remove additional problematic symbols
        text = re.sub(r'[✅❌⭐⚡▶️⏹️⏸️⏯️⏭️⏮️⏬⏫🔄🔃🔂🔁🔀↩️↪️⤴️⤵️]', ' ', text)

        # Keep only letters, numbers, basic punctuation, and essential symbols
        text = re.sub(r'[^\w\s.,!?:;()\-\'"°%&+=/]', ' ', text)

        return text

    def _normalize_spacing_and_punctuation(self, text: str) -> str:
        """Normalize spacing and punctuation"""
        # Fix spacing around punctuation
        text = re.sub(r'\s*([.,!?:;])\s*', r'\1 ', text)

        # Remove multiple consecutive punctuation
        text = re.sub(r'[.,!?:;]{2,}', '.', text)

        # Normalize multiple spaces
        text = re.sub(r'\s+', ' ', text)

        return text.strip()

    def _convert_time_formats(self, text: str) -> str:
        """Convert time formats to speech-friendly versions"""

        def time_replacer(match):
            hour = int(match.group(1))
            minute = int(match.group(2))
            period = match.group(3) if match.group(3) else ""

            hour_word = self._number_to_words(hour)

            if minute == 0:
                minute_part = ""
            elif minute < 10:
                minute_part = f" oh {self._number_to_words(minute)}"
            else:
                minute_part = f" {self._number_to_words(minute)}"

            period_part = f" {period.upper()}" if period else ""

            return f"{hour_word}{minute_part}{period_part}"

        # Match time patterns
        text = re.sub(r'(\d{1,2}):(\d{2})\s*(AM|PM|am|pm)?', time_replacer, text)
        return text

    def _convert_measurements(self, text: str) -> str:
        """Convert temperatures and measurements"""

        def temp_replacer(match):
            value = match.group(1)
            unit = match.group(2)

            value_words = self._convert_number_string(value)

            if unit.upper() == 'C':
                unit_name = "degrees Celsius"
            elif unit.upper() == 'F':
                unit_name = "degrees Fahrenheit"
            else:
                unit_name = f"degrees {unit}"

            return f"{value_words} {unit_name}"

        # Temperature patterns
        text = re.sub(r'([\d.]+)°([CFcf])', temp_replacer, text)

        return text

    def _convert_percentages(self, text: str) -> str:
        """Convert percentages to words"""

        def percent_replacer(match):
            number = match.group(1)
            number_words = self._convert_number_string(number)
            return f"{number_words} percent"

        text = re.sub(r'([\d.]+)\s*%', percent_replacer, text)
        return text

    def _convert_decimal_numbers(self, text: str) -> str:
        """Convert decimal numbers to words"""

        def decimal_replacer(match):
            return self._convert_number_string(match.group(1))

        text = re.sub(r'\b(\d+\.\d+)\b', decimal_replacer, text)
        return text

    def _convert_whole_numbers(self, text: str) -> str:
        """Convert reasonable whole numbers to words"""

        def number_replacer(match):
            number = int(match.group(1))
            # Only convert reasonable numbers (not IDs, years, etc.)
            if 1 <= number <= 100:
                return self._number_to_words(number)
            return str(number)

        text = re.sub(r'\b(\d{1,3})\b', number_replacer, text)
        return text

    def _expand_abbreviations_and_devices(self, text: str) -> str:
        """Expand abbreviations and device names"""
        # Time abbreviations
        text = re.sub(r'\bAM\b', 'A M', text, flags=re.IGNORECASE)
        text = re.sub(r'\bPM\b', 'P M', text, flags=re.IGNORECASE)

        # Device normalizations
        for device, normalized in self.device_normalizations.items():
            pattern = rf'\b{re.escape(device)}\b'
            text = re.sub(pattern, normalized, text, flags=re.IGNORECASE)

        return text

    def _handle_special_characters(self, text: str) -> str:
        """Handle remaining special characters"""
        replacements = {
            '&': ' and ',
            '+': ' plus ',
            '=': ' equals ',
            '/': ' slash ',
            '@': ' at '
        }

        for symbol, word in replacements.items():
            text = text.replace(symbol, word)

        return text

    def _final_cleanup(self, text: str) -> str:
        """Final cleanup and validation"""
        # Remove extra spaces
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()

        # Ensure proper sentence ending
        if text and not text.endswith(('.', '!', '?')):
            text += '.'

        # Limit length for TTS (prevent very long responses)
        if len(text) > 300:
            sentences = text.split('.')
            result = ""
            for sentence in sentences:
                if len(result + sentence) < 280:
                    result += sentence + "."
                else:
                    break
            text = result.rstrip('.') + '.'

        return text

    def _convert_number_string(self, num_str: str) -> str:
        """Convert number string to words"""
        try:
            if '.' in num_str:
                whole, decimal = num_str.split('.')
                whole_words = self._number_to_words(int(whole))
                decimal_words = ' '.join(self._number_to_words(int(d)) for d in decimal)
                return f"{whole_words} point {decimal_words}"
            else:
                return self._number_to_words(int(num_str))
        except (ValueError, IndexError):
            return num_str

    def _number_to_words(self, number: int) -> str:
        """Convert integer to words"""
        if number == 0:
            return "zero"

        if number < 0:
            return f"negative {self._number_to_words(abs(number))}"

        if number < 20:
            return self.ones[number]

        if number < 100:
            tens_digit = number // 10
            ones_digit = number % 10
            if ones_digit == 0:
                return self.tens[tens_digit]
            else:
                return f"{self.tens[tens_digit]} {self.ones[ones_digit]}"

        if number < 1000:
            hundreds_digit = number // 100
            remainder = number % 100
            result = f"{self.ones[hundreds_digit]} hundred"
            if remainder > 0:
                result += f" {self._number_to_words(remainder)}"
            return result

        # For larger numbers, return as string
        return str(number)

    def _clean_persian_text(self, text: str) -> str:
        """Clean Persian text for TTS"""
        # Convert Persian digits
        text = text.translate(self.persian_to_english)

        # Remove emojis but preserve Persian characters
        persian_pattern = re.compile(
            r'[^\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF'
            r'\w\s.,!?()\'"-]+'
        )
        text = persian_pattern.sub(' ', text)

        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def _basic_fallback_cleaning(self, text: str) -> str:
        """Basic fallback if main cleaning fails"""
        text = re.sub(r'[^\w\s.,!?()-]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()

        if text and not text.endswith(('.', '!', '?')):
            text += '.'

        return text

    def _speak(self, text: str, is_persian: bool = False):
        """Speak text using TTS with enhanced cleaning"""
        if not text.strip():
            return

        try:
            # Set speaking flag to prevent audio feedback
            self.is_speaking = True
            print(f"🗣️ Speaking: '{text}'")

            # Auto-detect language if not specified
            if not is_persian:
                is_persian = self.assistant.persian_service.is_persian(text)

            lang = 'fa' if is_persian else 'en'

            # Create TTS
            tts = gTTS(text=text, lang=lang, slow=False)

            # Temporary file handling
            temp_path = None
            try:
                # Create temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
                    temp_path = temp_file.name
                    tts.save(temp_path)

                # Stop any previous audio before playing new
                pygame.mixer.music.stop()
                time.sleep(0.1)  # Brief pause

                # Play audio
                pygame.mixer.music.load(temp_path)
                pygame.mixer.music.play()

                # Wait for completion
                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(10)

            finally:
                # Cleanup with retry logic
                if temp_path and os.path.exists(temp_path):
                    try:
                        # Ensure audio is stopped
                        pygame.mixer.music.stop()
                        time.sleep(0.1)
                        os.unlink(temp_path)
                    except PermissionError:
                        # File may still be in use, try again after a delay
                        time.sleep(0.5)
                        try:
                            os.unlink(temp_path)
                        except:
                            logger.warning(f"Could not delete temporary file: {temp_path}")

        except Exception as e:
            logger.error(f"TTS error: {e}")
            print(f"❌ Could not speak response: {e}")
        finally:
            time.sleep(0.5)
            self.is_speaking = False

    def _wait_for_speech_complete(self):
        """Wait for any ongoing speech to complete"""
        while self.is_speaking or pygame.mixer.music.get_busy():
            time.sleep(0.1)

    def _pause_listening(self):
        """Temporarily pause voice detection"""
        self.listening_paused = True
        print("🔇 Pausing voice detection...")

    def _resume_listening(self):
        """Resume voice detection"""
        self.listening_paused = False
        print("🔊 Resuming voice detection...")

    def stop_listening(self):
        """Stop the voice interface"""
        self.is_listening = False
        self.is_recording_command = False
        self.is_speaking = False

        # Stop audio stream
        if hasattr(self, 'audio_stream'):
            try:
                self.audio_stream.stop()
                self.audio_stream.close()
            except:
                pass

        # Stop any playing audio
        try:
            pygame.mixer.music.stop()
        except:
            pass

        print("🔇 Voice interface stopped")

    def get_status(self) -> dict:
        """Get voice interface status"""
        return {
            'listening': self.is_listening,
            'recording_command': self.is_recording_command,
            'paused': self.listening_paused,
            'speaking': self.is_speaking,
            'wake_words': self.wake_words,
            'buffer_size': len(self.audio_buffer),
            'noise_level': self.noise_level,
            'enhanced_cleaning': True,
            'whisper_loaded': self.whisper_model is not None
        }
