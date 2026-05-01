from pydantic_settings import BaseSettings
from pydantic import Field
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # Railway provides DATABASE_URL automatically when MySQL plugin is added
    DATABASE_URL: str = Field(default=os.getenv("DATABASE_URL", ""))
    
    # JWT settings
    SECRET_KEY: str = Field(default=os.getenv("SECRET_KEY", "your-secret-key-change-this"))
    ALGORITHM: str = Field(default=os.getenv("ALGORITHM", "HS256"))
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")))
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Important: ignore extra env vars

settings = Settings()

# Ensure DATABASE_URL uses correct driver for pymysql
if settings.DATABASE_URL and "mysql://" in settings.DATABASE_URL:
    # Replace mysql:// with mysql+pymysql:// for SQLAlchemy
    settings.DATABASE_URL = settings.DATABASE_URL.replace("mysql://", "mysql+pymysql://")