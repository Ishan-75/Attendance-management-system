import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.middleware import SecurityHeadersMiddleware, setup_exception_handlers
from app.api.v1.router import api_router
from app.db.session import SessionLocal
from app.db.init_db import init_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("attendance.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure database tables exist & seed baseline data
    logger.info("Verifying and initializing database on startup...")
    db = SessionLocal()
    try:
        init_db(db)
        logger.info("Database tables and baseline seeds verified successfully.")
    except Exception as e:
        logger.error(f"Critical error during startup database initialization: {e}", exc_info=True)
        raise e
    finally:
        db.close()
    yield
    # Shutdown
    logger.info("Application shutting down...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Enterprise Employee Attendance Management System API",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan
)

# 1. Security Headers Middleware
app.add_middleware(SecurityHeadersMiddleware)

# 2. CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else [settings.CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# 3. Setup sanitized exception handlers
setup_exception_handlers(app)

# 4. Mount API v1 router
app.include_router(api_router, prefix=settings.API_V1_STR)


# Root health shortcut
@app.get("/health", tags=["Health"])
def root_health():
    return {
        "status": "ok",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION
    }
