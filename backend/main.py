from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import time
import yaml
import os
from contextlib import asynccontextmanager

from .database.db import init_database
from .database.vector_store import init_vector_store
from .api.routes import router as api_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting Sovereign AI Arsenal...")
    
    try:
        # Load configuration
        with open('config.yaml', 'r') as file:
            config = yaml.safe_load(file)
        
        # Initialize database
        init_database()
        logger.info("Database initialized")
        
        # Initialize vector store
        vector_store_config = config.get('vector_store', {})
        init_vector_store(vector_store_config)
        logger.info("Vector store initialized")
        
        # Create logs directory
        os.makedirs('logs', exist_ok=True)
        
        logger.info("Sovereign AI Arsenal started successfully")
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Sovereign AI Arsenal...")

# Create FastAPI application
app = FastAPI(
    title="Sovereign AI Arsenal",
    description="Production-grade AI intelligence platform for discovering and analyzing AI repositories",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)

cors_origins = config.get('api', {}).get('cors_origins', ["*"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# Include API routes
app.include_router(api_router)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check database connection
        from .database.db import db
        with db.get_session() as session:
            session.execute("SELECT 1")
        
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Sovereign AI Arsenal",
        "description": "Production-grade AI intelligence platform",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

# Metrics endpoint
@app.get("/metrics")
async def metrics():
    """Basic metrics endpoint"""
    try:
        from .database.db import db
        from .database.models import Repository, Classification
        
        with db.get_session() as session:
            total_repos = session.query(Repository).count()
            total_classifications = session.query(Classification).count()
            
            # Get recent activity
            from datetime import datetime, timedelta
            recent_repos = session.query(Repository).filter(
                Repository.updated_at >= datetime.utcnow() - timedelta(days=7)
            ).count()
        
        return {
            "total_repositories": total_repos,
            "total_classifications": total_classifications,
            "recent_activity": recent_repos,
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get metrics")

if __name__ == "__main__":
    import uvicorn
    
    # Get configuration
    host = config.get('api', {}).get('host', '0.0.0.0')
    port = config.get('api', {}).get('port', 8000)
    debug = config.get('api', {}).get('debug', False)
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    )