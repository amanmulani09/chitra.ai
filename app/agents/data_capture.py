import base64
import os
import tempfile

from app.config import OPENAI_API_KEY, logger, openai_client
from app.models.schemas import CapturedData

class DataCaptureAgent:
    """
    Data Capture Agent is responsible for receiving video frames and audio,
    then processing them into a format suitable for analysis.
    Create the DataCaptureAgent class:
    """

    def __init__(self):
        self.name = "DataCaptureAgent"

    async def process_audio(self, audio_base64: str) -> str:
        """Transcribe audio using OpenAI Whisper"""
        try:
            if not OPENAI_API_KEY:
                return "Audio transcription unavailable - API key not configured"
            # Handle different audio formats
            if ',' in audio_base64:
                audio_data = base64.b64decode(audio_base64.split(',')[1])
            else:
                audio_data = base64.b64decode(audio_base64)
            # Create temporary file for Whisper API
            with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name
            try:
                # Use OpenAI Whisper for transcription
                with open(temp_file_path, 'rb') as audio_file:
                    transcript = await openai_client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        language="en"
                    )
                return transcript.text if transcript.text else "No speech detected"
            finally:
                # Clean up temp file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
        except Exception as e:
            logger.error(f"Audio processing error: {str(e)}")
            return f"Audio processing error: {str(e)}"
        
    async def validate_image(self, image_base64: str) -> bool:
        """Validate image quality and format"""
        try:
            if not image_base64 or len(image_base64) < 100:
                return False
            # Check if it's a valid base64 image
            if 'data:image' not in image_base64:
                return False
            return True
        except Exception:
            return False
        
    async def capture_and_process(self, image_base64: str, audio_base64: str, timestamp: str) -> CapturedData:
        """Main capture and processing function"""
        logger.info("Starting data capture and processing")
        # Validate image
        if not await self.validate_image(image_base64):
            raise ValueError("Invalid image data")
        # Process audio
        transcription = await self.process_audio(audio_base64)
        # Determine capture quality
        quality = "high" if len(transcription) > 10 and "error" not in transcription.lower() else "medium"
        # Create captured data
        captured_data = CapturedData(
            image_data=image_base64,
            audio_transcription=transcription,
            timestamp=timestamp,
            capture_quality=quality
        )
        logger.info("Data capture and processing completed successfully")
        return captured_data