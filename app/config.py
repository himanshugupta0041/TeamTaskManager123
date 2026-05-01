from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv
import urllib.parse

load_dotenv()

class Settings(BaseSettings):
    # First try to get Railway's DATABASE_URL, otherwise fall back to local
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    
    # If DATABASE_URL is not set, construct from individual MySQL variables (Railway provides these)
    if not DATABASE_URL:
        MYSQL_HOST = os.getenv("MYSQLHOST", os.getenv("MYSQL_HOST", "localhost"))
        MYSQL_PORT = os.getenv("MYSQLPORT", os.getenv("MYSQL_PORT", "3306"))
        MYSQL_USER = os.getenv("MYSQLUSER", os.getenv("MYSQL_USER", "root"))
        MYSQL_PASSWORD = os.getenv("MYSQLPASSWORD", os.getenv("MYSQL_PASSWORD", "2004"))
        MYSQL_DATABASE = os.getenv("MYSQLDATABASE", os.getenv("MYSQL_DATABASE", "task_manager"))
        
        # URL encode password to handle special characters
        encoded_password = urllib.parse.quote_plus(MYSQL_PASSWORD)
        DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{encoded_password}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
    
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production-123456789")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()