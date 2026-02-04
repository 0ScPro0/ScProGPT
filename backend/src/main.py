from contextlib import asynccontextmanager
from fastapi import FastAPI
import uvicorn

from core.config import settings
from api.v1.router import router
from database import database

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="AI Chat API", lifespan=lifespan)
app.include_router(router)

if __name__ == "__main__":
    uvicorn.run(
        app="main:app",
        host=settings.server.host,
        port=settings.server.port,
        reload=settings.server.reload
    )