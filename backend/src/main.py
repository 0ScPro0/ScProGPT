from fastapi import FastAPI
import uvicorn

from core.config import settings
from api.v1.router import router

app = FastAPI(title="AI Chat API")
app.include_router(router)

if __name__ == "__main__":
    uvicorn.run(
        app,
        host=settings.server.host,
        port=settings.server.port,
        reload=settings.server.reload
    )