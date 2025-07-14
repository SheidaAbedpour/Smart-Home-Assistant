import numpy as np
import sounddevice as sd
import threading
import queue
import time
import logging
import re
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
    Complete voice interface for Smart Home Assistant

    Features:
    - Wake word detection
    - Speech-to-text with Whisper
    - Text-to-speech with gTTS
    - Voice activity detection
    - Multilingual support
    - Audio feedback prevention
    """

    def __init__(self, assistant: SmartHomeAssistant):
        """Initialize voice interface"""
        self.assistant = assistant
        self.wake_words = ["hey assistant", "hey"]

        # Audio settings
        self.sample_rate = 16000
        self.chunk_size = 1024

        # State management
        self.is_listening = False
        self.is_recording_command = False
        self.listening_paused = False
        self.is_speaking = False  # NEW: Track when TTS is active

        # Audio processing
        self.audio_queue = queue.Queue()
        self.command_queue = queue.Queue()
        self.audio_buffer = []

        # Voice components
        self.whisper_model = None
        self.noise_level = 0.0
        self.vad_threshold = 0.003  # LOWERED: More sensitive detection

        # Threading
        self.command_lock = threading.Lock()

        # Initialize components
        self._initialize_voice_components()

    def _initialize_voice_components(self):
        """Initialize voice recognition components"""
        try:
            print("🔄 Loading voice components...")

            # Initialize Whisper
            print("   📥 Loading Whisper model (this may take a moment)...")
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
        """Start the voice interface"""
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
            print("💡 Try: 'Hey assistant, turn on the kitchen lamp'")
            print("💡 Or in Persian: 'Hey assistant, چراغ آشپزخانه را روشن کن'")
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
        """Show voice interface welcome"""
        print("\n" + "🎤" + "=" * 58 + "🎤")
        print("          SMART HOME ASSISTANT - VOICE CONTROL")
        print("🎤" + "=" * 58 + "🎤")
        print("🌍 Multilingual Support: English + Persian")
        print("👂 Wake Words: " + ", ".join(f"'{w}'" for w in self.wake_words))
        print("🗣️  Speech-to-Text: OpenAI Whisper")
        print("🔊 Text-to-Speech: Google TTS")
        print("🎤" + "=" * 58 + "🎤")

    def _start_audio_stream(self):
        """Start audio input stream"""
        try:
            def audio_callback(indata, frames, time_info, status):
                if not self.is_listening:
                    return

                audio_data = indata[:, 0] if len(indata.shape) > 1 else indata.flatten()

                # FIXED: Don't process audio when speaking (prevents feedback)
                if self.is_speaking:
                    return

                # Always add to command queue if recording
                if self.is_recording_command:
                    self.command_queue.put(audio_data.copy())

                # Only process for wake words when not paused
                if not self.listening_paused:
                    max_vol = np.max(np.abs(audio_data))
                    # DEBUGGING: Lower threshold for better sensitivity
                    if max_vol > 0.002:  # Lowered from 0.005
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

                # FIXED: Skip processing if speaking
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
                    # Check for wake words if we have enough audio
                    if len(self.audio_buffer) >= self.sample_rate * 2:  # 2 seconds
                        self._check_for_wake_word()

            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Audio processing error: {e}")

    def _detect_voice_activity(self, audio_chunk: np.ndarray) -> bool:
        """Simple voice activity detection with debugging"""
        try:
            # FIXED: Don't detect voice when speaking
            if self.is_speaking:
                return False

            # Calculate RMS volume
            volume = np.sqrt(np.mean(audio_chunk ** 2))

            # Update noise level estimate
            if self.noise_level == 0.0:
                self.noise_level = volume
            else:
                self.noise_level = self.noise_level * 0.95 + volume * 0.05

            # DEBUGGING: Lower threshold and add more verbose output
            threshold = max(0.005, self.noise_level * 2)  # Lowered threshold
            voice_detected = volume > threshold

            # DEBUGGING: Show more information
            if voice_detected:
                print(f"🎤 Voice detected! Vol: {volume:.4f}, Threshold: {threshold:.4f}, Noise: {self.noise_level:.4f}")
            elif volume > 0.001:  # Show quiet sounds too
                print(f"🔇 Audio detected but below threshold: {volume:.4f} < {threshold:.4f}", end="\r", flush=True)

            return voice_detected

        except Exception as e:
            logger.error(f"VAD error: {e}")
            return False

    def _check_for_wake_word(self):
        """Check recent audio for wake words with debugging"""
        try:
            # Skip if already recording or speaking
            if self.is_recording_command or self.is_speaking:
                return

            # Get recent audio (last 3 seconds)
            recent_samples = min(self.sample_rate * 3, len(self.audio_buffer))
            if recent_samples < self.sample_rate:  # Need at least 1 second
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

            # DEBUGGING: More flexible wake word detection
            text_words = text.split()
            for wake_word in self.wake_words:
                wake_parts = wake_word.lower().split()

                # Check if all parts of wake word are in the text
                if all(part in text for part in wake_parts):
                    print(f"🎯 Wake word detected: '{wake_word}' in '{text}'")
                    self._handle_wake_word()
                    return

                # Also check for partial matches
                for part in wake_parts:
                    if part in text and len(part) > 2:  # Only for meaningful parts
                        print(f"⚠️ Partial wake word match: '{part}' found in '{text}'")

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

        # FIXED: Wait for TTS to finish before resuming
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
                # FIXED: Wait for any TTS to complete before resuming
                self._wait_for_speech_complete()
                print("✅ Ready for next wake word...")

    def _process_voice_command(self, audio_data: np.ndarray):
        """Process recorded voice command"""
        try:
            # Recognize speech
            result = self.whisper_model.transcribe(
                audio_data,
                language='en',  # Let Whisper auto-detect
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
                        print(f"🤖 Response: {response}")

                        # Clean response for TTS
                        clean_response = self._clean_response_for_speech(response)
                        self._speak(clean_response)
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

    def _clean_response_for_speech(self, response: str) -> str:
        """Clean response text for better TTS"""
        # Remove excessive emojis and formatting
        response = re.sub(r'[^\w\s.,!?()-]', '', response)

        # Replace common patterns
        response = response.replace('✅', 'Success:')
        response = response.replace('❌', 'Error:')
        response = response.replace('🔴', 'offline')
        response = response.replace('🟢', 'online')

        # Clean up whitespace
        response = re.sub(r'\s+', ' ', response).strip()

        # Limit length for better TTS
        if len(response) > 200:
            response = response[:197] + "..."

        return response

    def _speak(self, text: str):
        """Speak text using TTS with improved audio handling"""
        if not text.strip():
            return

        try:
            # FIXED: Set speaking flag to prevent audio feedback
            self.is_speaking = True
            print(f"🗣️ Speaking: '{text}'")

            # Detect language for TTS
            lang = 'fa' if self.assistant.persian_service.is_persian(text) else 'en'

            # Create TTS
            tts = gTTS(text=text, lang=lang)

            # FIXED: Better temporary file handling
            temp_path = None
            try:
                # Create temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
                    temp_path = temp_file.name
                    tts.save(temp_path)

                # FIXED: Stop any previous audio before playing new
                pygame.mixer.music.stop()
                time.sleep(0.1)  # Brief pause

                # Play audio
                pygame.mixer.music.load(temp_path)
                pygame.mixer.music.play()

                # Wait for completion
                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(10)

            finally:
                # FIXED: Cleanup with retry logic
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
            # FIXED: Always clear speaking flag and add buffer time
            time.sleep(0.5)  # Buffer time to prevent immediate audio pickup
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
            'audio_queue_size': self.audio_queue.qsize(),
            'noise_level': self.noise_level,
            'whisper_loaded': self.whisper_model is not None
        }
