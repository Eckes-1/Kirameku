from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse

from app.config import CORS_ORIGINS
from app.database import init_db
from app.api import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Kirameku Backend", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

uploads_dir = Path(__file__).resolve().parent.parent / "uploads"
uploads_dir.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")

admin_dist = Path(__file__).resolve().parent.parent / "admin" / "dist"
if admin_dist.exists():
    app.mount("/admin/static", StaticFiles(directory=str(admin_dist / "static")), name="admin-static")

    @app.get("/admin")
    @app.get("/admin/")
    async def admin_page():
        return FileResponse(str(admin_dist / "index.html"), media_type="text/html")

    @app.get("/admin/{filename:path}")
    async def admin_static(filename: str):
        file_path = admin_dist / filename
        if file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(admin_dist / "index.html"), media_type="text/html")


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/routes")
def get_routes():
    return {"code": 0, "message": "success", "data": []}
