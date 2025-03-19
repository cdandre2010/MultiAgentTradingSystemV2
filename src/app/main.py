from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Multi-Agent Trading System API",
    description="API for trading strategy creation, backtesting, and signal generation",
    version="2.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint to check if API is running."""
    return {"message": "Multi-Agent Trading System API V2"}

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "version": "2.0.0",
        # Add database connection status checks here once implemented
    }

# Import and include routers
# from .routers import auth, strategies, knowledge, backtest
# app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
# app.include_router(strategies.router, prefix="/api/strategies", tags=["Strategies"])
# app.include_router(knowledge.router, prefix="/api/knowledge", tags=["Knowledge Graph"])
# app.include_router(backtest.router, prefix="/api/backtest", tags=["Backtesting"])

# Add exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return {
        "status": "error",
        "code": exc.detail.get("code", "ERROR"),
        "message": exc.detail.get("message", str(exc.detail)),
        "details": exc.detail.get("details", {})
    }