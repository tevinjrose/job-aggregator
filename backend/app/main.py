from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.routers import jobs, scraper, sectors, settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="JobRadar", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}


app.include_router(jobs.router, prefix="/api/jobs", tags=["jobs"])
app.include_router(settings.router, prefix="/api/settings", tags=["settings"])
app.include_router(scraper.router, prefix="/api/scraper", tags=["scraper"])
app.include_router(sectors.router, prefix="/api/sectors", tags=["sectors"])
