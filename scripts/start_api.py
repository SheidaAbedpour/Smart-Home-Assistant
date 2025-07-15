import webbrowser
import time


def main():
    print("\n🚀 Starting Smart Home Assistant API Server")
    print("=" * 50)

    try:
        # Import and start the API server directly
        import uvicorn
        from api_server import app

        print("🌐 API Server: http://localhost:8000")
        print("📚 API Docs: http://localhost:8000/docs")
        print("=" * 50)

        # Open browser after a delay
        def open_browser():
            time.sleep(3)
            try:
                webbrowser.open("http://localhost:8000/docs")
                print("📚 Opened API docs in browser")
            except:
                pass

        import threading
        browser_thread = threading.Thread(target=open_browser, daemon=True)
        browser_thread.start()

        # Start the server (this will block)
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            log_level="info"
        )

    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()