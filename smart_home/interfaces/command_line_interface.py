import time
import sys
from typing import Optional
from smart_home.core.assistant import SmartHomeAssistant


class CLIInterface:
    """Enhanced command line interface for Smart Home Assistant"""

    def __init__(self, assistant: SmartHomeAssistant):
        """Initialize CLI interface"""
        self.assistant = assistant
        self.conversation_history = []
        self.max_history = 10

    def run(self):
        """Run the enhanced CLI interface"""
        self._show_welcome()
        self._show_quick_start()

        while True:
            try:
                # Get user input with enhanced prompt
                user_input = self._get_user_input()

                # Handle special commands
                if self._handle_special_commands(user_input):
                    continue

                # Process command
                if user_input:
                    self._process_and_display_command(user_input)

            except KeyboardInterrupt:
                self._handle_exit()
                break
            except Exception as e:
                print(f"❌ Error: {e}")

    def _show_welcome(self):
        """Show enhanced welcome message"""
        print("\n" + "🎭" + "=" * 58 + "🎭")
        print("           SMART HOME ASSISTANT - TEXT CHAT")
        print("🎭" + "=" * 58 + "🎭")
        print("🌍 Automatic Language Detection: English + Persian")
        print("🤖 Powered by LLaMA 3.3 70B with Function Calling")
        print("📱 Connected to your smart home devices")
        print("🎭" + "=" * 58 + "🎭")

    def _show_quick_start(self):
        """Show quick start guide"""
        examples = self.assistant.get_example_commands()

        print("\n🚀 QUICK START - Try these commands:")
        print("\n🇺🇸 English Examples:")
        for i, cmd in enumerate(examples["english"][:3], 1):
            print(f"   {i}. {cmd}")

        print("\n🇮🇷 Persian Examples:")
        for i, cmd in enumerate(examples["persian"][:3], 1):
            print(f"   {i}. {cmd}")

        print("\n💡 Special Commands:")
        print("   • 'help' - Show all commands")
        print("   • 'status' - Show device status")
        print("   • 'history' - Show conversation history")
        print("   • 'clear' - Clear screen")
        print("   • 'quit' / 'خروج' - Exit to main menu")
        print("\n" + "-" * 60)

    def _get_user_input(self) -> str:
        """Get user input with enhanced prompt"""
        try:
            # Show typing indicator
            print("\n🎤", end=" ", flush=True)
            user_input = input("You / شما: ").strip()
            return user_input
        except EOFError:
            return "quit"

    def _handle_special_commands(self, user_input: str) -> bool:
        """Handle special CLI commands"""
        command = user_input.lower()

        if command in ['quit', 'exit', 'bye', 'خروج', 'بای', 'خداحافظ']:
            self._handle_exit()
            return True

        elif command == 'help':
            self._show_help()
            return True

        elif command == 'status':
            self._show_device_status()
            return True

        elif command == 'history':
            self._show_conversation_history()
            return True

        elif command == 'clear':
            self._clear_screen()
            return True

        elif command == 'test':
            self._run_service_test()
            return True

        elif command == 'examples':
            self._show_more_examples()
            return True

        return False

    def _process_and_display_command(self, user_input: str):
        """Process command and display response with enhancements"""
        # Show processing indicator
        self._show_processing_indicator()

        # Process command
        start_time = time.time()
        response = self.assistant.process_command(user_input)
        processing_time = time.time() - start_time

        # Add to conversation history
        self._add_to_history(user_input, response)

        # Display response with formatting
        self._display_response(response, processing_time)

    def _show_processing_indicator(self):
        """Show animated processing indicator"""
        indicators = ["🤔 Processing", "🤔 Processing.", "🤔 Processing..", "🤔 Processing..."]
        for indicator in indicators:
            print(f"\r{indicator}", end="", flush=True)
            time.sleep(0.3)
        print("\r" + " " * 20 + "\r", end="", flush=True)  # Clear line

    def _display_response(self, response: str, processing_time: float):
        """Display response with enhanced formatting"""
        print("🤖 Assistant / دستیار:")
        print(response)
        print(f"⏱️  Processed in {processing_time:.2f}s")

    def _wrap_text(self, text: str, width: int) -> list:
        """Wrap text to specified width"""
        words = text.split()
        lines = []
        current_line = ""

        for word in words:
            if len(current_line + " " + word) <= width:
                current_line += (" " + word) if current_line else word
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)

        return lines or [""]

    def _add_to_history(self, user_input: str, response: str):
        """Add interaction to conversation history"""
        self.conversation_history.append({
            "timestamp": time.time(),
            "user_input": user_input,
            "response": response
        })

        # Keep only recent conversations
        if len(self.conversation_history) > self.max_history:
            self.conversation_history.pop(0)

    def _show_help(self):
        """Show comprehensive help"""
        print("\n📚 SMART HOME ASSISTANT - HELP")
        print("=" * 50)

        print("\n🏠 Device Control:")
        print("   • Turn on/off: 'Turn on kitchen lamp' / 'چراغ آشپزخانه را روشن کن'")
        print("   • Brightness: 'Set lamp to 70%' / 'چراغ را روی ۷۰ درصد تنظیم کن'")
        print("   • Temperature: 'Set AC to 22 degrees' / 'کولر را روی ۲۲ درجه تنظیم کن'")
        print("   • TV Control: 'Turn on TV' / 'تلویزیون را روشن کن'")
        print("   • All devices: 'Turn off all devices' / 'همه دستگاه‌ها را خاموش کن'")

        print("\n🌐 Information Services:")
        print("   • Weather: 'What's the weather?' / 'هوا چطوره؟'")
        print("   • News: 'Get technology news' / 'خبرهای فناوری بده'")
        print("   • Time: 'What time is it?' / 'ساعت چنده؟'")

        print("\n💬 CLI Commands:")
        print("   • help - Show this help")
        print("   • status - Show device status")
        print("   • history - Show conversation history")
        print("   • examples - Show more examples")
        print("   • test - Test all services")
        print("   • clear - Clear screen")
        print("   • quit - Return to main menu")

        print("\n🎯 Tips:")
        print("   • Commands work in both English and Persian")
        print("   • Language is detected automatically")
        print("   • Use natural language - be conversational!")

    def _show_device_status(self):
        """Show current device status"""
        print("\n📊 Current Device Status:")
        print("=" * 50)
        status = self.assistant.get_device_status()
        print(status)

    def _show_conversation_history(self):
        """Show recent conversation history"""
        print("\n💭 Recent Conversation History:")
        print("=" * 50)

        if not self.conversation_history:
            print("No conversation history yet.")
            return

        for i, conv in enumerate(self.conversation_history[-5:], 1):
            timestamp = time.strftime("%H:%M:%S", time.localtime(conv["timestamp"]))
            print(f"\n{i}. [{timestamp}]")
            print(f"   You: {conv['user_input']}")
            response_preview = conv['response']
            print(f"   Assistant: {response_preview}")

    def _run_service_test(self):
        """Run comprehensive service test"""
        print("\n🧪 Testing All Services...")
        print("=" * 50)

        test_results = self.assistant.test_services()
        for service, result in test_results.items():
            print(f"{service.capitalize()}: {result}")

    def _show_more_examples(self):
        """Show comprehensive examples"""
        examples = self.assistant.get_example_commands()

        print("\n🎯 Comprehensive Command Examples:")
        print("=" * 50)

        print("\n🇺🇸 English Commands:")
        for i, cmd in enumerate(examples["english"], 1):
            print(f"   {i}. {cmd}")

        print("\n🇮🇷 Persian Commands:")
        for i, cmd in enumerate(examples["persian"], 1):
            print(f"   {i}. {cmd}")

        print("\n💡 Advanced Examples:")
        print("   • 'Set kitchen lamp to blue color at 80% brightness'")
        print("   • 'Turn on AC in room 1 with cool mode and low fan speed'")
        print("   • 'What's the weather in Paris and set AC accordingly'")
        print("   • 'چراغ حمام را قرمز کن و روشنی‌اش را ۵۰ درصد تنظیم کن'")

    def _clear_screen(self):
        """Clear the screen"""
        import os
        os.system('cls' if os.name == 'nt' else 'clear')
        self._show_welcome()

    def _handle_exit(self):
        """Handle graceful exit"""
        print("\n👋 Thanks for using Smart Home Assistant!")
        print("🔄 Returning to main menu...")
        time.sleep(1)
