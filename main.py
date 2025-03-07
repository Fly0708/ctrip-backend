import app.config
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.ctripapi import router as ctrip_router
from app.log import logger

app = FastAPI(debug=True)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ctrip_router)


@app.middleware("http")
async def log_requests(request, call_next):
    logger.info(f"Incoming request: {request.method} {request.url}")
    try:
        response = await call_next(request)
    except Exception as exc:
        logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
        raise
    logger.info(f"Outgoing response: {response.status_code}")
    return response
