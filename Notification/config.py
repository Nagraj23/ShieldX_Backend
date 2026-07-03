import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Base Cluster Connections
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    
    MONGO_URI: str = "mongodb://localhost:27017"
    DB_NAME: str = "notification_service"

    # Fallback Integrations
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_PHONE_NUMBER: str = ""

    # Delivery Scaling Rules
    MAX_DELIVERY_ATTEMPTS: int = 3
    INITIAL_RETRY_DELAY_SECONDS: int = 30

    @property
    def redis_url(self) -> str:
        """Constructs a uniform Redis connection signature string."""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/0"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()