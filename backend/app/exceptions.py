import logging
from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger("notas-api")


async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Error interno no manejado: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )
