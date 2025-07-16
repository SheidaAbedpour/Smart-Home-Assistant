from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import logging
import json
import base64
from datetime import datetime
import tempfile
import os

try:
    import whisper
    import numpy as np
    from gtts import gTTS
    import pygame

    VOICE_AVAILABLE = True
except ImportError:
    VOICE_AVAILABLE = False
    logging.warning("Voice dependencies not installed. Voice features will be disabled.")

from smart_home.core.assistant import SmartHomeAssistant

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Smart Home Assistant API with Voice Support",
    description="Multilingual Smart Home Control API with Voice Interface",
    version="2.0.0"
)

# Enhanced CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize assistant and voice components
try:
    assistant = SmartHomeAssistant()
    logger.info("✅ Smart Home Assistant initialized")
except Exception as e:
    logger.error(f"❌ Failed to initialize assistant: {e}")
    assistant = None

# Initialize voice recognition if available
whisper_model = None
if VOICE_AVAILABLE:
    try:
        logger.info("🎤 Loading Whisper model for voice recognition...")
        whisper_model = whisper.load_model("base")
        pygame.mixer.init()
        logger.info("✅ Voice components initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize voice components: {e}")
        VOICE_AVAILABLE = False


# Request/Response models
class CommandRequest(BaseModel):
    command: str
    language: Optional[str] = "auto"
    voice_enabled: Optional[bool] = False


class CommandResponse(BaseModel):
    response: str
    success: bool
    language_detected: Optional[str] = None
    audio_base64: Optional[str] = None


class VoiceCommandRequest(BaseModel):
    audio_base64: str
    language: Optional[str] = "auto"


class VoiceStatus(BaseModel):
    voice_available: bool
    whisper_loaded: bool
    tts_available: bool
    supported_languages: List[str]


# Helper functions
def clean_text_for_tts(text: str, is_persian: bool = False) -> str:
    """Clean text for TTS synthesis"""
    import re

    # Remove emojis and special characters
    text = re.sub(r'[^\w\s\u0600-\u06FF.,!?()-]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()

    # Convert temperatures
    text = re.sub(r'(\d+)°[CF]', r'\1 degrees', text)

    # Convert percentages
    text = re.sub(r'(\d+)%', r'\1 percent', text)

    if not text.endswith(('.', '!', '?')):
        text += '.'

    return text


async def generate_audio_response(text: str, language: str = "en") -> Optional[str]:
    """Generate audio response using TTS"""
    if not VOICE_AVAILABLE:
        return None

    try:
        # Clean text for TTS
        is_persian = language == "fa" or (assistant and assistant.persian_service.is_persian(text))
        clean_text = clean_text_for_tts(text, is_persian)

        if not clean_text.strip():
            return None

        # Generate TTS
        lang_code = 'fa' if is_persian else 'en'
        tts = gTTS(text=clean_text, lang=lang_code, slow=False)

        # Save to temporary file and encode to base64
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
            tts.save(temp_file.name)

            with open(temp_file.name, "rb") as audio_file:
                audio_data = audio_file.read()
                audio_base64 = base64.b64encode(audio_data).decode()

            # Clean up
            os.unlink(temp_file.name)

            return audio_base64

    except Exception as e:
        logger.error(f"Error generating audio response: {e}")
        return None


def is_device_command(command: str) -> bool:
    """Check if command is device-related"""
    device_keywords = ['turn', 'set', 'روشن', 'خاموش', 'تنظیم', 'lamp', 'چراغ', 'ac', 'کولر', 'tv', 'تلویزیون']
    return any(keyword in command.lower() for keyword in device_keywords)


# API Routes
@app.get("/")
async def root():
    """Health check with voice capability info"""
    return {
        "message": "Smart Home Assistant API with Voice Support",
        "status": "running",
        "assistant_ready": assistant is not None,
        "voice_available": VOICE_AVAILABLE,
        "whisper_loaded": whisper_model is not None,
        "version": "2.0.0",
        "websocket_support": False
    }


@app.get("/api/voice/status", response_model=VoiceStatus)
async def get_voice_status():
    """Get voice capabilities status"""
    return VoiceStatus(
        voice_available=VOICE_AVAILABLE,
        whisper_loaded=whisper_model is not None,
        tts_available=VOICE_AVAILABLE,
        supported_languages=["en", "fa"] if VOICE_AVAILABLE else []
    )


@app.post("/api/command", response_model=CommandResponse)
async def process_command(request: CommandRequest):
    """Process natural language command with optional voice response"""
    if not assistant:
        raise HTTPException(status_code=500, detail="Assistant not initialized")

    try:
        logger.info(f"🎤 Received command: '{request.command}' (voice_enabled: {request.voice_enabled})")

        # Process command with assistant
        response = assistant.process_command(request.command)

        if response is None:
            response = "Assistant returned no response"
        elif response == "":
            response = "Assistant returned empty response"

        # Detect language
        is_persian = assistant.persian_service.is_persian(request.command)
        detected_language = "persian" if is_persian else "english"

        # Generate audio response if requested and voice is available
        audio_base64 = None
        if request.voice_enabled and VOICE_AVAILABLE and response:
            audio_base64 = await generate_audio_response(
                response,
                "fa" if is_persian else "en"
            )

        return CommandResponse(
            response=str(response),
            success=True,
            language_detected=detected_language,
            audio_base64=audio_base64
        )

    except Exception as e:
        logger.error(f"❌ Error processing command: {e}")
        import traceback
        traceback.print_exc()

        return CommandResponse(
            response=f"Error: {str(e)}",
            success=False
        )


@app.post("/api/voice/command", response_model=CommandResponse)
async def process_voice_command(request: VoiceCommandRequest):
    """Process voice command from audio data"""
    if not VOICE_AVAILABLE or not whisper_model:
        raise HTTPException(status_code=501, detail="Voice processing not available")

    if not assistant:
        raise HTTPException(status_code=500, detail="Assistant not initialized")

    try:
        logger.info("🎤 Processing voice command...")

        # Decode audio from base64
        audio_data = base64.b64decode(request.audio_base64)

        # Save to temporary file for Whisper
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            temp_file.write(audio_data)
            temp_file_path = temp_file.name

        try:
            # Transcribe with Whisper
            result = whisper_model.transcribe(temp_file_path, language=None)
            transcript = result["text"].strip()

            if not transcript:
                return CommandResponse(
                    response="I couldn't understand the audio. Please try again.",
                    success=False
                )

            logger.info(f"📝 Transcribed: '{transcript}'")

            # Process the transcribed command
            response = assistant.process_command(transcript)

            if response is None:
                response = "Command processed successfully"
            elif response == "":
                response = "Command completed"

            # Detect language
            is_persian = assistant.persian_service.is_persian(transcript)
            detected_language = "persian" if is_persian else "english"

            # Generate audio response
            audio_base64 = await generate_audio_response(
                response,
                "fa" if is_persian else "en"
            )

            return CommandResponse(
                response=f"🎤 \"{transcript}\" → {response}",
                success=True,
                language_detected=detected_language,
                audio_base64=audio_base64
            )

        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    except Exception as e:
        logger.error(f"❌ Error processing voice command: {e}")
        return CommandResponse(
            response=f"Error processing voice command: {str(e)}",
            success=False
        )


@app.get("/api/devices")
async def get_all_devices():
    """Get status of all devices"""
    if not assistant:
        raise HTTPException(status_code=500, detail="Assistant not initialized")

    try:
        logger.info("📱 Getting all devices...")
        all_devices = assistant.device_manager.get_all_devices()

        devices = {"lamps": [], "acs": [], "tvs": []}

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
            return {"success": False, "message": f"Device {device_id} not found"}

        result = device.toggle()

        return {"success": True, "message": result}

    except Exception as e:
        logger.error(f"Error toggling device {device_id}: {e}")
        return {"success": False, "message": f"Error: {str(e)}"}


@app.get("/api/status")
async def get_system_status():
    """Get system status including voice capabilities"""
    if not assistant:
        raise HTTPException(status_code=500, detail="Assistant not initialized")

    try:
        status = assistant.get_system_status()
        # Add voice status
        status["voice"] = {
            "available": VOICE_AVAILABLE,
            "whisper_loaded": whisper_model is not None,
            "tts_available": VOICE_AVAILABLE,
            "supported_languages": ["en", "fa"] if VOICE_AVAILABLE else []
        }
        status["websocket_support"] = False
        return status
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return {"error": "Endpoint not found", "message": "This endpoint does not exist"}


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return {"error": "Internal server error", "message": "Something went wrong on the server"}


if __name__ == "__main__":
    import uvicorn

    print("\n🚀 Smart Home Assistant API Server (Simplified - No WebSockets)")
    print("=" * 70)
    print("🌐 API Server: http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/docs")
    print("🎤 Voice Support:", "✅ Enabled" if VOICE_AVAILABLE else "❌ Disabled")
    print("🔌 WebSocket Support: ❌ Disabled (use polling instead)")
    print("=" * 70)

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
