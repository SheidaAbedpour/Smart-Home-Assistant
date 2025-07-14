import sys

from smart_home.core.assistant import SmartHomeAssistant
from smart_home.interfaces.command_line_interface import CLIInterface


def main():
    """Run the CLI interface directly"""
    try:
        print("🔄 Initializing Smart Home Assistant...")

        # Initialize the assistant
        assistant = SmartHomeAssistant()

        # Create and run the CLI
        cli = CLIInterface(assistant)
        cli.run()

    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Make sure GROQ_API_KEY is set in your .env file")
        sys.exit(1)


if __name__ == "__main__":
    main()
