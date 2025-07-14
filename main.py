import sys
import logging
from smart_home.config.app_config import my_config
from smart_home.core.assistant import SmartHomeAssistant

# Configure logging
logging.basicConfig(
    level=getattr(logging, my_config.log_level, logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def show_banner():
    """Show application banner"""
    print("\n🚀 SMART HOME ASSISTANT")
    print("=" * 50)
    print("🌍 Multilingual (English + Persian)")
    print("🤖 LLM-Powered with Function Calling")
    print("🎤 Voice + CLI Interfaces")
    print("=" * 50)


def show_menu() -> str:
    """Show main menu"""
    print("\n🎯 Choose interface:")
    print("1. 💬 Enhanced CLI Interface")
    print("2. 🎤 Voice Interface")
    print("3. ❌ Exit")
    return input("\nSelect option (1-3): ").strip()


def run_cli_interface(assistant: SmartHomeAssistant):
    """Run enhanced CLI interface"""
    try:
        from smart_home.interfaces.command_line_interface import CLIInterface

        print("\n💬 Starting Enhanced CLI Interface...")
        cli = CLIInterface(assistant)
        cli.run()

    except ImportError:
        print("❌ CLI interface not found")
        print("💡 Make sure command_line_interface.py is in smart_home/interfaces/")
    except Exception as e:
        logger.error(f"CLI interface error: {e}")
        print(f"❌ CLI interface error: {e}")


def run_voice_interface(assistant: SmartHomeAssistant):
    """Run voice interface"""
    # Check dependencies
    try:
        import whisper
        import sounddevice
        import pygame
        import numpy
        from gtts import gTTS
    except ImportError as e:
        missing = str(e).split("No module named")[-1].strip().strip("'\"")
        print(f"❌ Missing dependency: {missing}")
        print("\n💡 Install voice dependencies:")
        print("pip install openai-whisper sounddevice gtts pygame numpy scipy")
        print("\n🔧 System dependencies:")
        print("Ubuntu/Debian: sudo apt-get install portaudio19-dev python3-pyaudio")
        print("macOS: brew install portaudio")
        return

    try:
        from smart_home.interfaces.voice_interface import VoiceInterface

        print("\n🎤 Starting Voice Interface...")
        print("👂 Say 'Hey assistant' followed by your command")
        print("💡 Press Ctrl+C to stop")

        voice = VoiceInterface(assistant)
        voice.run()

    except ImportError:
        print("❌ Voice interface not found")
        print("💡 Make sure voice_interface.py is in smart_home/interfaces/")
    except Exception as e:
        logger.error(f"Voice interface error: {e}")
        print(f"❌ Voice interface error: {e}")


def main():
    """Main application entry point"""
    show_banner()

    # Initialize assistant
    try:
        print("\n🔄 Initializing Smart Home Assistant...")
        assistant = SmartHomeAssistant()

        # Main loop
        while True:
            choice = show_menu()

            if choice == "1":
                run_cli_interface(assistant)
            elif choice == "2":
                run_voice_interface(assistant)
            elif choice == "3":
                print("\n👋 Thanks for using Smart Home Assistant!")
                assistant.shutdown()
                break
            else:
                print("❌ Invalid option. Please choose 1-3.")

    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        logger.error(f"Application error: {e}")
        print(f"\n❌ Failed to start Smart Home Assistant:")
        print(f"Error: {e}")
        print(f"\n💡 Common solutions:")
        print(f"   • Check GROQ_API_KEY in .env file")
        print(f"   • Get free key from: https://console.groq.com")


if __name__ == "__main__":
    main()
