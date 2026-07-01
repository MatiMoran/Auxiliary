import secrets
import logging
from pydantic_settings import BaseSettings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("notas-api")


class Settings(BaseSettings):
    database_url: str = "sqlite:///./notas.db"
    api_key: str = ""
    debug: bool = False

    model_config = {
        "env_file": ".env",
        "env_prefix": "NOTAS_",
        "case_sensitive": False,
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.api_key:
            self.api_key = secrets.token_urlsafe(32)
            logger.info("⚡ API Key generada automáticamente")
            logger.info("⚡ NOTAS_API_KEY=%s", self.api_key)
            logger.info("⚡ Guárdala en .env si querés mantenerla entre reinicios")


settings = Settings()
