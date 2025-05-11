from fastapi import FastAPI
from app.routers.scan import router as scan_router
from app.routers.status import router as status_router
from common.messaging import RabbitPublisher
from app.config import settings
from app.logger import logger

app = FastAPI(
    title="Acarelia Gateway API",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.include_router(scan_router, prefix="/api", tags=["scan"])
app.include_router(status_router, prefix="/api", tags=["status"])

@app.on_event("startup")
async def startup_event():
    logger.info("Gateway API starting up...")
    app.state.rabbitPublisher = RabbitPublisher(settings.RABBITMQ_URL)
    await app.state.rabbitPublisher.connect()
    logger.info("RabbitPublisher connected")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Gateway API shutting down...")
    try:
        await app.state.rabbitPublisher._conn.close()
    except Exception:
        pass

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}