import torch
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from loguru import logger

from src.users.api.routes import router as access_control_router
from src.food_catalogue.api.router import router as food_router
from src.tracking.api.router import router as tracking_router
from src.ai.api.router import router as ai_router, get_audio_service, get_vision_service
from src.meal_planning.api.router import router as meal_planning_router
from src.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.models_ready = False
    logger.info("Preloading AI models...")

    if torch.cuda.is_available():
        logger.info(f"CUDA Available: True")
        logger.info(f"Device Name: {torch.cuda.get_device_name(0)}")
    else:
        logger.warning("CUDA Available: False - Running on CPU")

    try:
        service = get_audio_service()
        await service.warmup()
        vision_service = get_vision_service()

        logger.info("AI models preloaded successfully!")
    except Exception as e:
        logger.warning(f"Failed to preload AI models: {e}")

    app.state.models_ready = True
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(access_control_router)
app.include_router(food_router, prefix="/api/v1/foods", tags=["Food Catalogue"])
app.include_router(tracking_router, prefix="/api/v1/tracking", tags=["Tracking"])
app.include_router(ai_router, prefix="/api/v1/ai", tags=["AI Processing"])
app.include_router(meal_planning_router, prefix="/api/v1", tags=["Meal Planning"])


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/health")
async def health():
    if not getattr(app.state, "models_ready", False):
        return JSONResponse(status_code=503, content={"status": "loading"})
    return {"status": "ok"}
