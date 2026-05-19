from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import outfit
from dotenv import load_dotenv
from config import settings
from middleware.rate_limiter import RateLimiterMiddleware
from routers import dna

# Load environment variables from .env file
load_dotenv()

app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered outfit recommendation system",
    version=settings.APP_VERSION
)

# Allow requests from React frontend during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RateLimiterMiddleware)

app.include_router(outfit.router, prefix="/outfit", tags=["outfit"])
app.include_router(dna.router, prefix="/outfit", tags=["dna"])


@app.get("/health")
async def health_check():
    # Basic health check endpoint to verify the API is running
    return {"status": "ok", "app": settings.APP_NAME}