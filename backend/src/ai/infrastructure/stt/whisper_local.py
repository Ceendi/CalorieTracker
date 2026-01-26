import tempfile
import os
import asyncio
from typing import Optional, Any, cast
from loguru import logger

from src.ai.infrastructure.stt.base import BaseSTTClient
from src.ai.domain.exceptions import TranscriptionFailedException, AudioFormatError
from src.ai.config import WHISPER_INITIAL_PROMPT, WHISPER_CONFIG

_whisper_model = None
_model_lock = asyncio.Lock()


class WhisperLocalClient(BaseSTTClient):
    SUPPORTED_FORMATS = {".mp3", ".wav", ".m4a", ".ogg", ".flac", ".webm", ".mp4"}
    
    def __init__(self, model_size: str = "medium"):
        self.model_size = model_size
        self._model: Optional[object] = None
        
    async def _get_model(self):
        global _whisper_model
        
        async with _model_lock:
            if _whisper_model is None:
                logger.info(f"Loading Whisper model: {self.model_size}")
                _whisper_model = await asyncio.to_thread(self._load_model)
                logger.info("Whisper model loaded successfully")
            
            return _whisper_model
            
    async def load_model(self) -> Any:
        return await self._get_model()
    
    def _load_model(self):
        try:
            import whisper
            import torch
            
            device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Using device: {device}")
            
            model = whisper.load_model(self.model_size, device=device)
            return model
            
        except ImportError as e:
            logger.error(f"Whisper not installed: {e}")
            raise TranscriptionFailedException(
                "Whisper is not installed. Run: pip install openai-whisper"
            )
    
    async def transcribe(self, audio_bytes: bytes, language: str = "pl") -> str:
        if len(audio_bytes) == 0:
            raise AudioFormatError("Empty audio file")
        
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".m4a", delete=False) as temp_file:
                temp_file.write(audio_bytes)
                temp_path = temp_file.name
            
            model = await self._get_model()

            # silence linter mis-interpreting whisper signature
            model_any = cast(Any, model)
            
            result = await asyncio.to_thread(
                model_any.transcribe,
                audio=temp_path,
                language=language,
                initial_prompt=WHISPER_INITIAL_PROMPT,
                **WHISPER_CONFIG
            )
            
            transcription = result.get("text", "").strip()
            
            if not transcription:
                logger.warning("Whisper returned empty transcription")
                raise TranscriptionFailedException("No speech detected in audio")
            
            logger.info(f"Transcription successful: '{transcription[:100]}...'")
            return transcription
            
        except TranscriptionFailedException:
            raise
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            raise TranscriptionFailedException(f"Transcription failed: {str(e)}")
        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except Exception as e:
                    logger.warning(f"Failed to cleanup temp file: {e}")
    
    @classmethod
    def is_available(cls) -> bool:
        try:
            import whisper
            return True
        except ImportError:
            return False
    
    @classmethod
    def get_device_info(cls) -> dict:
        try:
            import torch
            return {
                "cuda_available": torch.cuda.is_available(),
                "cuda_device_count": torch.cuda.device_count() if torch.cuda.is_available() else 0,
                "cuda_device_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
            }
        except ImportError:
            return {"error": "PyTorch not installed"}
