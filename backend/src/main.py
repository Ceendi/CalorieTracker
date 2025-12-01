from fastapi import FastAPI

from src.access_control.api.routes import router as access_control_router
from src.food_catalogue.api.router import router as food_router
from src.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
)

app.include_router(access_control_router)
app.include_router(food_router)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/health")
async def health():
    return {"status": "ok"}
