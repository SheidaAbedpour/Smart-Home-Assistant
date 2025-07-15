from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import logging

from smart_home.core.assistant import SmartHomeAssistant

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Smart Home Assistant API",
    description="Multilingual Smart Home Control API",
    version="1.0.0"
)

# Allow requests from Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for local development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize your assistant
try:
    assistant = SmartHomeAssistant()
    logger.info("✅ Smart Home Assistant initialized")
except Exception as e:
    logger.error(f"❌ Failed to initialize assistant: {e}")
    assistant = None


# Request/Response models
class CommandRequest(BaseModel):
    command: str
    language: Optional[str] = "auto"


class CommandResponse(BaseModel):
    response: str
    success: bool
    language_detected: Optional[str] = None


# API Routes
@app.get("/")
async def root():
    """Health check"""
    return {
        "message": "Smart Home Assistant API",
        "status": "running",
        "assistant_ready": assistant is not None
    }


@app.post("/api/command", response_model=CommandResponse)
async def process_command(request: CommandRequest):
    """Process natural language command"""
    if not assistant:
        logger.error("Assistant not initialized")
        raise HTTPException(status_code=500, detail="Assistant not initialized")

    try:
        logger.info(f"🎤 Received command: '{request.command}'")
        logger.info(f"📝 Command length: {len(request.command)} characters")

        # Use your existing assistant
        logger.info("🧠 Processing with assistant...")
        response = assistant.process_command(request.command)

        logger.info(f"🤖 Assistant response: '{response}'")
        logger.info(f"📏 Response length: {len(response) if response else 0} characters")
        logger.info(f"🔍 Response type: {type(response)}")

        # Check if response is None or empty
        if response is None:
            logger.warning("⚠️ Assistant returned None")
            response = "Assistant returned no response"
        elif response == "":
            logger.warning("⚠️ Assistant returned empty string")
            response = "Assistant returned empty response"

        # Detect language
        is_persian = assistant.persian_service.is_persian(request.command)
        detected_language = "persian" if is_persian else "english"

        logger.info(f"🌍 Detected language: {detected_language}")

        # Create response object
        response_obj = CommandResponse(
            response=str(response),  # Ensure it's a string
            success=True,
            language_detected=detected_language
        )

        logger.info(f"📤 Sending response: {response_obj.dict()}")

        return response_obj

    except Exception as e:
        logger.error(f"❌ Error processing command '{request.command}': {e}")
        import traceback
        traceback.print_exc()

        error_response = CommandResponse(
            response=f"Error: {str(e)}",
            success=False
        )

        logger.info(f"📤 Sending error response: {error_response.dict()}")
        return error_response


@app.get("/api/devices")
async def get_all_devices():
    """Get status of all devices"""
    if not assistant:
        raise HTTPException(status_code=500, detail="Assistant not initialized")

    try:
        logger.info("📱 Getting all devices...")
        all_devices = assistant.device_manager.get_all_devices()
        logger.info(f"📱 Found {len(all_devices)} devices")

        devices = {
            "lamps": [],
            "acs": [],
            "tvs": []
        }

        for device_id, device in all_devices.items():
            device_info = {
                "id": device_id,
                "name": device.name,
                "location": device.location,
                "type": device.device_type,
                "power": device.state.get("power", False),
                "online": device.is_online
            }

            if device.device_type == "lamp":
                device_info.update({
                    "brightness": device.state.get("brightness", 100),
                    "color": device.state.get("color", "white")
                })
                devices["lamps"].append(device_info)

            elif device.device_type == "ac":
                device_info.update({
                    "temperature": device.state.get("temperature", 22),
                    "mode": device.state.get("mode", "cool"),
                    "fan_speed": device.state.get("fan_speed", "medium")
                })
                devices["acs"].append(device_info)

            elif device.device_type == "tv":
                device_info.update({
                    "channel": device.state.get("channel", 1),
                    "volume": device.state.get("volume", 50),
                    "input": device.state.get("input", "hdmi1")
                })
                devices["tvs"].append(device_info)

        logger.info(
            f"📱 Returning devices: {len(devices['lamps'])} lamps, {len(devices['acs'])} ACs, {len(devices['tvs'])} TVs")
        return devices

    except Exception as e:
        logger.error(f"Error getting devices: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/devices/{device_id}/toggle")
async def toggle_device(device_id: str):
    """Toggle device power"""
    if not assistant:
        raise HTTPException(status_code=500, detail="Assistant not initialized")

    try:
        logger.info(f"🔄 Toggling device: {device_id}")
        device = assistant.device_manager.get_device(device_id)
        if not device:
            logger.warning(f"⚠️ Device not found: {device_id}")
            return {
                "success": False,
                "message": f"Device {device_id} not found"
            }

        result = device.toggle()
        logger.info(f"✅ Device {device_id} toggled: {result}")

        return {
            "success": True,
            "message": result
        }

    except Exception as e:
        logger.error(f"Error toggling device {device_id}: {e}")
        return {
            "success": False,
            "message": f"Error: {str(e)}"
        }


@app.get("/api/status")
async def get_system_status():
    """Get system status"""
    if not assistant:
        raise HTTPException(status_code=500, detail="Assistant not initialized")

    try:
        return assistant.get_system_status()
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    print("\n🚀 Smart Home Assistant API Server (Debug Version)")
    print("=" * 60)
    print("🌐 API Server: http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/docs")
    print("=" * 60)

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")