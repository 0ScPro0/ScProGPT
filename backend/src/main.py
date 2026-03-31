from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from core.config import settings
from api.v1.router import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="ScProGPT", lifespan=lifespan)
app.include_router(router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.server.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    uvicorn.run(
        app="main:app",
        host=settings.server.host,
        port=settings.server.port,
        reload=settings.server.reload,
    )
