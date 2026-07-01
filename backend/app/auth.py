from fastapi import Header, HTTPException
from app.config import settings
import hmac


async def verify_api_key(x_api_key: str = Header(...)):
    if not hmac.compare_digest(x_api_key, settings.api_key):
        raise HTTPException(status_code=401, detail="Invalid API Key")
