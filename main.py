import sys
import logging
from typing import Optional
from smart_home.config.app_config import my_config
from smart_home.core.assistant import SmartHomeAssistant

# Configure logging
logging.basicConfig(
    level=getattr(logging, "INFO", logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def show_banner():
    """Show application banner"""
    print("\n🚀 SMART HOME ASSISTANT")
    print("=" * 50)
    print("🌍 Multilingual (English + Persian)")
    print("🤖 LLM-Powered with Function Calling")
    print("🎤 Voice + Text Interfaces")
    print("=" * 50)


def show_menu() -> str:
    """Show main menu and get user choice"""
    print("\n🎯 Choose an interface:")
    print("1. 💬 Text Chat (English + Persian)")
    print("2. 🎤 Voice Interface (with wake words)")
    print("3. 📊 System Status & Test")
    print("4. 🧪 Test All Services")
    print("5. ❌ Exit")
    return input("\nSelect option (1-5): ").strip()


def run_text_interface(assistant: SmartHomeAssistant):
    """Run text-based chat interface"""
    print("\n💬 Text Chat Interface Started!")
    print("🌍 Automatic language detection (English + Persian)")

    # Show example commands
    examples = assistant.get_example_commands()
    print("\n🎯 Example commands:")
    print("English:")
    for cmd in examples["english"][:3]:
        print(f"  • {cmd}")
    print("Persian:")
    for cmd in examples["persian"][:3]:
        print(f"  • {cmd}")

    print("\n💡 Type 'quit', 'exit', or 'خروج' to return to menu")
    print("-" * 60)

    while True:
        try:
            user_input = input("\n🎤 You / شما: ").strip()

            # Check for exit commands
            if user_input.lower() in ['quit', 'exit', 'bye', 'خروج', 'بای', 'خداحافظ']:
                print("👋 Returning to main menu...")
                break

            if not user_input:
                continue

            # Process command
            print("🤔 Processing...")
            response = assistant.process_command(user_input)
            print(f"🤖 Assistant / دستیار: {response}")

        except KeyboardInterrupt:
            print("\n👋 Returning to main menu...")
            break
        except Exception as e:
            logger.error(f"Error in text interface: {e}")
            print(f"❌ Error: {e}")


def run_voice_interface(assistant: SmartHomeAssistant):
    """Run voice interface"""
    try:
        from smart_home.interfaces.voice_interface import VoiceInterface

        print("\n🎤 Starting Voice Interface...")
        voice_interface = VoiceInterface(assistant)
        voice_interface.run()

    except ImportError as e:
        print(f"\n❌ Voice interface dependencies missing:")
        print(f"Error: {e}")
        print("\n💡 To enable voice interface:")
        print("pip install openai-whisper sounddevice gtts pygame numpy")
        print("\nSystem dependencies may also be needed:")
        print("Ubuntu/Debian: sudo apt-get install portaudio19-dev python3-pyaudio")
        print("macOS: brew install portaudio")
    except Exception as e:
        logger.error(f"Voice interface error: {e}")
        print(f"❌ Voice interface error: {e}")


def show_system_status(assistant: SmartHomeAssistant):
    """Show comprehensive system status"""
    print("\n📊 System Status:")
    print("=" * 50)

    status = assistant.get_system_status()

    # Device information
    print(f"🏠 Devices: {status['total_devices']} total, {status['powered_on']} powered on")
    device_types = status['device_types']
    print(f"   💡 Lamps: {device_types['lamps']}")
    print(f"   ❄️  ACs: {device_types['acs']}")
    print(f"   📺 TVs: {device_types['tvs']}")

    # Services status
    print(f"\n🌐 Services:")
    services = status['services']
    for service_name, service_status in services.items():
        print(f"   {service_name.capitalize()}: {service_status}")

    # Language support
    languages = ", ".join(status['languages'])
    print(f"\n🌍 Languages: {languages}")

    # Configuration
    config_info = status['configuration']
    print(f"\n⚙️  Configuration:")
    print(f"   Default City: {config_info['default_city']}")
    print(f"   Debug Mode: {config_info['debug_mode']}")
    print(f"   Log Level: {config_info['log_level']}")

    # Show device status
    print(f"\n📱 Current Device Status:")
    device_status = assistant.get_device_status()
    print(device_status)


def test_all_services(assistant: SmartHomeAssistant):
    """Test all services"""
    print("\n🧪 Testing All Services...")
    print("=" * 50)

    test_results = assistant.test_services()

    for service_name, result in test_results.items():
        status_icon = "✅" if result.startswith("✅") else "❌"
        print(f"{status_icon} {service_name.capitalize()}: {result}")

    print("\n💡 If any services show errors:")
    print("   • Check your .env file for API keys")
    print("   • Verify internet connection")
    print("   • Check logs for detailed error messages")


def main():
    """Main application entry point"""
    show_banner()

    # Initialize assistant
    try:
        print("\n🔄 Initializing Smart Home Assistant...")
        assistant = SmartHomeAssistant()

        # Main application loop
        while True:
            choice = show_menu()

            if choice == "1":
                run_text_interface(assistant)
            elif choice == "2":
                run_voice_interface(assistant)
            elif choice == "3":
                show_system_status(assistant)
            elif choice == "4":
                test_all_services(assistant)
            elif choice == "5":
                print("\n👋 Thanks for using Smart Home Assistant!")
                assistant.shutdown()
                break
            else:
                print("❌ Invalid option. Please choose 1-5.")

    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        logger.error(f"Application error: {e}")
        print(f"\n❌ Failed to start Smart Home Assistant:")
        print(f"Error: {e}")
        print(f"\n💡 Common solutions:")
        print(f"   • Check that GROQ_API_KEY is set in .env file")
        print(f"   • Verify .env file exists (copy from .env.example)")
        print(f"   • Get free API key from: https://console.groq.com")


if __name__ == "__main__":
    main()
