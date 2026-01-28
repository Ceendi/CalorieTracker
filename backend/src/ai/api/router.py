import json
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from loguru import logger

from src.ai.application.audio_service import AudioProcessingService
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

# Singleton audio service instance (pgvector mode)
_audio_service_pgvector: Optional[AudioProcessingService] = None

# Legacy singleton (in-memory mode, deprecated)
_audio_service_legacy: Optional[AudioProcessingService] = None
_fineli_products: Optional[list] = None


def _load_fineli_products() -> list:
    """
    Load Fineli products from JSON files.

    .. deprecated:: 2.0.0
        This function is only used for legacy in-memory search mode.
        With pgvector mode, products are stored in the database.
    """
    global _fineli_products

    if _fineli_products is not None:
        return _fineli_products

    seeds_path = Path(__file__).parent.parent.parent.parent / "seeds" / "fineli_products.json"
    patch_path = Path(__file__).parent.parent.parent.parent / "seeds" / "staples_patch.json"

    products = []

    if seeds_path.exists():
        try:
            with open(seeds_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                products = data.get("products", [])
        except Exception as e:
            logger.error(f"Failed to load Fineli products: {e}")

    if patch_path.exists():
        try:
            with open(patch_path, "r", encoding="utf-8") as f:
                patch = json.load(f)
                products.extend(patch)
                logger.info(f"Merged {len(patch)} generic staples from patch file.")
        except Exception as e:
            logger.error(f"Failed to load Staples Patch: {e}")

    _fineli_products = products
    logger.info(f"Total products loaded: {len(_fineli_products)}")
    return _fineli_products


def get_audio_service() -> AudioProcessingService:
    """
    Get singleton AudioProcessingService instance using pgvector mode.

    This replaces the old in-memory search with database-backed pgvector
    hybrid search for better search quality and lower memory usage.

    Returns:
        AudioProcessingService configured for pgvector mode
    """
    global _audio_service_pgvector

    if _audio_service_pgvector is None:
        whisper_size = getattr(settings, "WHISPER_MODEL_SIZE", "medium")

        _audio_service_pgvector = AudioProcessingService(
            fineli_products=None,  # Not needed for pgvector mode
            whisper_model_size=whisper_size,
            use_pgvector=True
        )

        logger.info("AudioProcessingService initialized (pgvector mode)")

    return _audio_service_pgvector


def get_audio_service_legacy() -> AudioProcessingService:
    """
    Get legacy AudioProcessingService using in-memory search.

    .. deprecated:: 2.0.0
        Use get_audio_service() instead for pgvector mode.
        This function is kept for backward compatibility and testing.
    """
    global _audio_service_legacy

    if _audio_service_legacy is None:
        fineli_products = _load_fineli_products()

        whisper_size = getattr(settings, "WHISPER_MODEL_SIZE", "medium")

        _audio_service_legacy = AudioProcessingService(
            fineli_products=fineli_products,
            whisper_model_size=whisper_size,
            use_pgvector=False
        )

        if fineli_products:
            logger.info("Indexing products for Semantic Search Engine (legacy mode)...")
            _audio_service_legacy.vector_engine.index_products(fineli_products)

        logger.info("AudioProcessingService initialized (legacy in-memory mode)")

    return _audio_service_legacy


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

    **Search mode:** Uses pgvector-backed hybrid search for better accuracy
    compared to the legacy in-memory search.
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

        # Pass session for pgvector-based search
        result = await service.process_audio(
            audio_bytes=audio_bytes,
            language=language,
            session=session
        )

        logger.info(
            f"Processed audio: {result.meal_type} with {len(result.items)} items "
            f"in {result.processing_time_ms:.0f}ms (pgvector mode)"
        )

        return result

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


@router.get(
    "/status",
    summary="Get AI processing system status",
    description="Check availability of Whisper, SLM (Bielik), and vector engine."
)
async def get_status(
    service: AudioProcessingService = Depends(get_audio_service)
):
    return service.get_system_status()
