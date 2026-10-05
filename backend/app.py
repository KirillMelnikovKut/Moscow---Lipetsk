"""FastAPI application assembly and optional frontend hosting."""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from backend.api import router as api_router
from backend.config import FRONTEND_DIST

app = FastAPI(title="Маршрут Москва — Липецк", version="0.2.0")
app.include_router(api_router)

if FRONTEND_DIST.is_dir():
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
else:
    @app.get("/")
    def frontend_missing():
        return {"message": "Соберите интерфейс: cd frontend && npm install && npm run build"}
