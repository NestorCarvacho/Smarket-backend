from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuracion de la aplicacion, leida desde variables de entorno / .env."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    PROJECT_NAME: str = "Grocery List API"
    API_V1_PREFIX: str = "/api/v1"

    DATABASE_URL: str = "mysql+aiomysql://grocery_user:grocery_password@localhost:3306/grocery_db"
    DATABASE_URL_SYNC: str = "mysql+pymysql://grocery_user:grocery_password@localhost:3306/grocery_db"

    JWT_SECRET_KEY: str = "change-this-secret-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 10080

    CORS_ORIGINS: str = "*"

    # URL publica del backend (links de compartir / join desde WhatsApp)
    PUBLIC_BASE_URL: str = "https://smarket-backend-vf3c.onrender.com"

    # Sin proveedor de email: devolver el codigo de reset en la respuesta de forgot-password.
    # Poner en false cuando configures envio de emails.
    EXPOSE_RESET_CODES: bool = True

    MAX_FAILED_LOGIN_ATTEMPTS: int = 3
    RESET_CODE_EXPIRE_MINUTES: int = 30

    @property
    def cors_origins_list(self) -> list[str]:
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
