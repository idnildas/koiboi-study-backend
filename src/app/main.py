from fastapi import FastAPI
from app.api.v1.routes import router as v1_router
from app.core.config import settings


def create_app() -> FastAPI:
    app = FastAPI(title=settings.APP_NAME)
    app.include_router(v1_router, prefix="/api/v1")
    return app


app = create_app()


@app.get("/")
async def root():
    return {"message": f"{settings.APP_NAME} is running"}
