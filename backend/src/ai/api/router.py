from pathlib import Path
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from loguru import logger

from src.ai.application.audio_service import AudioProcessingService
from src.ai.application.vision_service import VisionProcessingService
from src.ai.application.dto import ProcessedMealDTO
from src.ai.domain.exceptions import (
    AudioProcessingException,
    TranscriptionFailedException,
    AudioFormatError,
    AudioTooLongError
)
from src.core.config import settings
from src.core.database import DBSession

router = APIRouter()

_audio_service: Optional[AudioProcessingService] = None
_vision_service: Optional[VisionProcessingService] = None

def get_vision_service() -> VisionProcessingService:
    global _vision_service
    if _vision_service is None:
        _vision_service = VisionProcessingService()
        logger.info("VisionProcessingService initialized")
    return _vision_service


def get_audio_service() -> AudioProcessingService:
    """
    Get singleton AudioProcessingService instance.

    Uses pgvector-backed hybrid search for product matching.
    """
    global _audio_service

    if _audio_service is None:
        whisper_size = getattr(settings, "WHISPER_MODEL_SIZE", "medium")

        _audio_service = AudioProcessingService(
            whisper_model_size=whisper_size
        )

        logger.info("AudioProcessingService initialized")

    return _audio_service


MAX_FILE_SIZE = 25 * 1024 * 1024
MAX_AUDIO_DURATION = 60


@router.post(
    "/process-audio",
    response_model=ProcessedMealDTO,
    summary="Process voice recording and extract meal information",
    description="""
    Upload an audio recording of a meal description and receive structured meal data.

    **Workflow:**
    1. Audio is transcribed using local Whisper model
    2. Text is analyzed by SLM (Bielik-4.5B) for structure
    3. Ingredients are matched using pgvector Hybrid Search (Vector + FTS)

    **Supported formats:** mp3, wav, m4a, ogg, flac, webm
    """
)
async def process_audio_meal(
    session: DBSession,
    audio: UploadFile = File(
        ...,
        description="Audio file (mp3, wav, m4a, etc.)"
    ),
    language: str = "pl",
    service: AudioProcessingService = Depends(get_audio_service)
):
    if not audio.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided"
        )

    valid_extensions = {".mp3", ".wav", ".m4a", ".ogg", ".flac", ".webm", ".mp4"}
    file_ext = Path(audio.filename).suffix.lower()
    if file_ext not in valid_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file format. Supported: {', '.join(valid_extensions)}"
        )

    try:
        audio_bytes = await audio.read()

        if len(audio_bytes) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty audio file"
            )

        if len(audio_bytes) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size: {MAX_FILE_SIZE // 1024 // 1024}MB"
            )

        result = await service.process_audio(
            audio_bytes=audio_bytes,
            language=language,
            session=session
        )

        logger.info(
            f"Processed audio: {result.meal_type} with {len(result.items)} items "
            f"in {result.processing_time_ms:.0f}ms"
        )

        return result

    except HTTPException:
        raise
    except TranscriptionFailedException as e:
        logger.error(f"Transcription failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except AudioFormatError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except AudioTooLongError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except AudioProcessingException as e:
        logger.error(f"Audio processing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process audio. Please try again."
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.post(
    "/transcribe",
    summary="Transcribe audio only (no food extraction)",
    description="Useful for debugging or when only transcription is needed."
)
async def transcribe_audio(
    audio: UploadFile = File(..., description="Audio file"),
    language: str = "pl",
    service: AudioProcessingService = Depends(get_audio_service)
):
    try:
        audio_bytes = await audio.read()

        if len(audio_bytes) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty audio file"
            )

        text = await service.transcribe_only(audio_bytes, language)

        return {"transcription": text, "language": language}

    except HTTPException:
        raise
    except TranscriptionFailedException as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to transcribe audio"
        )


@router.post(
    "/process-image",
    response_model=ProcessedMealDTO,
    summary="Process food photo and extract meal information",
    description="""
    Upload a food photo and receive structured meal data.
    
    **Workflow:**
    1. Image analyzed by Gemini Flash 3.0 (Vision)
    2. Ingredients extracted with estimated weight and macros
    3. Ingredients matched against DB using Vector Search
    4. If DB match found -> DB macros used
    5. If NO DB match -> Gemini macros used (fallback)
    """
)
async def process_food_image(
    session: DBSession,
    image: UploadFile = File(..., description="Image file (jpg, png, webp)"),
    service: VisionProcessingService = Depends(get_vision_service)
):
    if not image.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
        
    valid_extensions = {".jpg", ".jpeg", ".png", ".webp", ".heic"}
    file_ext = Path(image.filename).suffix.lower()
    if file_ext not in valid_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid file format. Supported: {', '.join(valid_extensions)}"
        )
        
    try:
        image_bytes = await image.read()
        
        if len(image_bytes) == 0:
            raise HTTPException(status_code=400, detail="Empty image file")
            
        if len(image_bytes) > 10 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="File too large. Max 10MB")
            
        result = await service.process_image(image_bytes, session)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Image processing failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to process image. Please try again.")


@router.get(
    "/status",
    summary="Get AI processing system status",
    description="Check availability of Whisper, SLM (Bielik), Vision (Gemini), and search."
)
async def get_status(
    audio_service: AudioProcessingService = Depends(get_audio_service),
    vision_service: VisionProcessingService = Depends(get_vision_service)
):
    status = audio_service.get_system_status()
    status.update(vision_service.get_system_status())
    return status
