import sys
import os
import logging

from smart_home.core.assistant import SmartHomeAssistant

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def check_voice_dependencies():
    """Check if voice dependencies are installed"""
    missing_deps = []

    try:
        import whisper
    except ImportError:
        missing_deps.append("openai-whisper")

    try:
        import sounddevice
    except ImportError:
        missing_deps.append("sounddevice")

    try:
        import pygame
    except ImportError:
        missing_deps.append("pygame")

    try:
        from gtts import gTTS
    except ImportError:
        missing_deps.append("gtts")

    try:
        import numpy
    except ImportError:
        missing_deps.append("numpy")

    if missing_deps:
        print("❌ Missing voice dependencies:")
        for dep in missing_deps:
            print(f"   • {dep}")
        print(f"\n💡 Install with:")
        print(f"pip install {' '.join(missing_deps)}")
        print(f"\n🔧 System dependencies:")
        print(f"Ubuntu/Debian: sudo apt-get install portaudio19-dev python3-pyaudio")
        print(f"macOS: brew install portaudio")
        return False

    return True


def main():
    try:
        print("🔍 Checking voice dependencies...")
        if not check_voice_dependencies():
            sys.exit(1)

        print("🔄 Initializing Smart Home Assistant for Voice...")

        # Initialize the assistant
        assistant = SmartHomeAssistant()

        # Import and run voice interface
        from smart_home.interfaces.voice_interface import VoiceInterface

        print("🎤 Starting Voice Interface...")
        print("💡 Say 'Hey assistant' followed by your command")
        print("💡 Press Ctrl+C to stop")

        voice_interface = VoiceInterface(assistant)
        voice_interface.run()

    except KeyboardInterrupt:
        print("\n🔇 Voice interface stopped")
        print("👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")
        if "GROQ_API_KEY" in str(e):
            print("💡 Make sure GROQ_API_KEY is set in your .env file")
        sys.exit(1)


if __name__ == "__main__":
    main()