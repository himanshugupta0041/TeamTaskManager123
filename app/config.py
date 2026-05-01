from pydantic_settings import BaseSettings
from pydantic import Field
import os
from dotenv import load_dotenv
import urllib.parse

load_dotenv()

class Settings(BaseSettings):
    # Database settings
    DATABASE_URL: str = Field(default="")
    
    # JWT settings
    SECRET_KEY: str = Field(default="your-secret-key-change-this")
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"

settings = Settings()

# Build DATABASE_URL if not set
if not settings.DATABASE_URL:
    # Try to get individual MySQL variables from Railway
    MYSQL_HOST = os.getenv("MYSQLHOST", os.getenv("MYSQL_HOST", ""))
    MYSQL_PORT = os.getenv("MYSQLPORT", os.getenv("MYSQL_PORT", "3306"))
    MYSQL_USER = os.getenv("MYSQLUSER", os.getenv("MYSQL_USER", ""))
    MYSQL_PASSWORD = os.getenv("MYSQLPASSWORD", os.getenv("MYSQL_PASSWORD", ""))
    MYSQL_DATABASE = os.getenv("MYSQLDATABASE", os.getenv("MYSQL_DATABASE", ""))
    
    if MYSQL_HOST and MYSQL_USER and MYSQL_PASSWORD:
        encoded_password = urllib.parse.quote_plus(MYSQL_PASSWORD)
        settings.DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{encoded_password}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
        print(f"✓ Built DATABASE_URL from individual variables")
    else:
        # Fallback for local development
        settings.DATABASE_URL = "mysql+pymysql://root:2004@localhost:3306/task_manager"
        print("⚠️ Using local database configuration")

# Validate DATABASE_URL is not empty
if not settings.DATABASE_URL:
    raise ValueError("DATABASE_URL is not configured! Please add MySQL plugin to your Railway project.")

print(f"✓ Database configured (URL hidden for security)")