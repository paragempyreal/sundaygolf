import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Database configuration (still from env for initial connection)
    DATABASE_URL = os.getenv("DATABASE_URL")
    
    # Fallback values for environment variables (will be overridden by database config)
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me")

    # CORS Origins
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000")

    # App Port
    APP_PORT = os.getenv("APP_PORT", "5000")
    
    # These will be loaded from database at runtime (only those needed)
    POLL_INTERVAL_MINUTES = None
    
    @classmethod
    def load_from_database(cls, config_service):
        """Load configuration from database"""
        try:
            cls.POLL_INTERVAL_MINUTES = int(config_service.get_config('system.poll_interval_minutes') or 5)
            
            # Load secret keys
            secret_key = config_service.get_config('system.secret_key')
            if secret_key:
                cls.SECRET_KEY = secret_key
                
        except Exception as e:
            print(f"Warning: Could not load configuration from database: {e}")
            # Fall back to environment variables
            cls.POLL_INTERVAL_MINUTES = int(os.getenv("POLL_INTERVAL_MINUTES", "5"))

settings = Settings()
