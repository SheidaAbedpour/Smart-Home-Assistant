import subprocess
import threading
import time
import webbrowser
import os
import sys
from pathlib import Path


def start_api_server():
    """Start the Python API server"""
    print("🚀 Starting Python API server...")
    try:
        # Import and run the API server
        import uvicorn
        from api_server import app

        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            log_level="warning"  # Reduce noise
        )
    except Exception as e:
        print(f"❌ API server failed: {e}")


def start_nextjs_ui():
    """Start the Next.js UI"""
    print("🎨 Starting Next.js UI...")

    ui_path = Path("../ui")
    if not ui_path.exists():
        print("❌ UI folder not found!")
        return False

    try:
        # Check if dependencies are installed
        node_modules = ui_path / "node_modules"
        if not node_modules.exists():
            print("📦 Installing npm dependencies...")
            subprocess.run(["npm", "install"], cwd=ui_path, check=True)

        # Start Next.js
        subprocess.run(["npm", "run", "dev"], cwd=ui_path)

    except subprocess.CalledProcessError as e:
        print(f"❌ Next.js failed: {e}")
        return False
    except FileNotFoundError:
        print("❌ npm not found. Please install Node.js")
        return False


def main():
    """Run both servers"""
    print("\n🌐 Smart Home Assistant Web Interface")
    print("=" * 50)

    # Start API server in background thread
    api_thread = threading.Thread(target=start_api_server, daemon=True)
    api_thread.start()

    # Wait for API to start
    print("⏳ Waiting for API server...")
    time.sleep(3)

    # Check if API is running
    try:
        import requests
        response = requests.get("http://localhost:8000", timeout=2)
        print("✅ API server running on http://localhost:8000")
    except:
        print("⚠️  API server may still be starting...")

    # # Open browser to API docs
    # try:
    #     webbrowser.open("http://localhost:8000/docs")
    #     print("📚 API docs opened in browser")
    # except:
    #     pass

    print("\n🎨 Now starting Next.js UI...")
    print("📱 UI will be available at: http://localhost:3000")
    print("\n💡 Commands to try:")
    print("   • Turn on kitchen lamp")
    print("   • چراغ آشپزخانه را روشن کن")
    print("   • What's the weather?")
    print("\n⏸️  Press Ctrl+C to stop both servers")

    # Start Next.js (this will block until stopped)
    try:
        start_nextjs_ui()
    except KeyboardInterrupt:
        print("\n🛑 Stopping servers...")
        print("✅ Done!")


if __name__ == "__main__":
    main()
