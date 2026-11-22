from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = "postgresql+psycopg2://medscribe:medscribe@localhost:5432/medscribe"
    jwt_secret: str = "change-me"
    jwt_expire_minutes: int = 480
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    whisper_model: str = "base"
    whisper_compute_type: str = "int8"
    upload_dir: str = "./uploads"
    cors_origins: str = "http://localhost:3000"
    admin_email: str = "admin@example.com"
    admin_password: str = "admin12345"


settings = Settings()
