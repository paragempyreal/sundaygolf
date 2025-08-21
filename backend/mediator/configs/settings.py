import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Database configuration (still from env for initial connection)
    DATABASE_URL = os.getenv("DATABASE_URL")
    
    # Fallback values for environment variables (will be overridden by database config)
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me")
    
    # These will be loaded from database at runtime
    FULFIL_SUBDOMAIN = None
    FULFIL_API_KEY = None
    SHIPHERO_REFRESH_TOKEN = None
    SHIPHERO_OAUTH_URL = None
    SHIPHERO_API_BASE_URL = None
    POLL_INTERVAL_MINUTES = None
    
    @classmethod
    def load_from_database(cls, config_service):
        """Load configuration from database"""
        try:
            cls.FULFIL_SUBDOMAIN = config_service.get_config('fulfil.subdomain')
            cls.FULFIL_API_KEY = config_service.get_config('fulfil.api_key')
            cls.SHIPHERO_REFRESH_TOKEN = config_service.get_config('shiphero.refresh_token')
            cls.SHIPHERO_OAUTH_URL = config_service.get_config('shiphero.oauth_url')
            cls.SHIPHERO_API_BASE_URL = config_service.get_config('shiphero.api_base_url')
            cls.POLL_INTERVAL_MINUTES = int(config_service.get_config('system.poll_interval_minutes') or 5)
            
            # Load secret keys
            secret_key = config_service.get_config('system.secret_key')
            if secret_key:
                cls.SECRET_KEY = secret_key
                
        except Exception as e:
            print(f"Warning: Could not load configuration from database: {e}")
            # Fall back to environment variables
            cls.FULFIL_SUBDOMAIN = os.getenv("FULFIL_SUBDOMAIN")
            cls.FULFIL_API_KEY = os.getenv("FULFIL_API_KEY")
            cls.SHIPHERO_REFRESH_TOKEN = os.getenv("SHIPHERO_REFRESH_TOKEN")
            cls.SHIPHERO_OAUTH_URL = os.getenv("SHIPHERO_OAUTH_URL", "https://public-api.shiphero.com/oauth")
            cls.SHIPHERO_API_BASE_URL = os.getenv("SHIPHERO_API_BASE_URL", "https://public-api.shiphero.com")
            cls.POLL_INTERVAL_MINUTES = int(os.getenv("POLL_INTERVAL_MINUTES", "5"))

settings = Settings()
