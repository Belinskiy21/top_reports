from fastapi import FastAPI

from app.api.routes import router as health_router
from app.api.v1 import router

app = FastAPI(title="Top Reports")


app.include_router(health_router)
app.include_router(router)
