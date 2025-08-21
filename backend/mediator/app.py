from flask import Flask
from sqlalchemy import text
from mediator.configs.settings import settings
from mediator.database.db import engine, SessionLocal
from mediator.controllers.routes import routes
from mediator.services.fulfil_client import FulfilWrapper
from mediator.services.shiphero_client import ShipHeroClient
from mediator.controllers.sync_logic import SyncService
from mediator.controllers.scheduler import start as start_scheduler
from mediator.models.models import Base
from mediator.services.config_service import config_service
from mediator.services.user_service import user_service

def initialize_database():
    """Initialize database with default configuration and admin user"""
    db = SessionLocal()
    try:
        print("Initializing database configuration...")
        
        # Initialize default configuration
        config_service.initialize_default_config(db)
        print("✅ Default configuration initialized")
        
        # Ensure secret keys are set
        config_service.ensure_secret_keys(db)
        print("✅ Secret keys ensured")
        
        # Initialize default admin user
        user_service.initialize_default_admin(db)
        print("✅ Default admin user initialized")
        
        # Load configuration into settings
        settings.load_from_database(config_service)
        print("✅ Configuration loaded from database")
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        db.rollback()
    finally:
        db.close()

def create_app():
    app = Flask(__name__)
    
    # Enable CORS
    from flask_cors import CORS
    CORS(app)
    
    # Ensure DB connectivity early
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))

    # Create tables if running without Alembic (dev convenience)
    Base.metadata.create_all(bind=engine)
    
    # Initialize database configuration and admin user
    initialize_database()
    
    # Set secret key from database
    app.config['SECRET_KEY'] = settings.SECRET_KEY

    # Register the routes blueprint
    app.register_blueprint(routes, url_prefix='/api')

    # Wire clients and service with current configuration
    fulfil = FulfilWrapper(settings.FULFIL_SUBDOMAIN, settings.FULFIL_API_KEY)
    shiphero = ShipHeroClient(settings.SHIPHERO_REFRESH_TOKEN, settings.SHIPHERO_OAUTH_URL, settings.SHIPHERO_API_BASE_URL)
    svc = SyncService(fulfil, shiphero)

    # Start scheduler with proper error handling
    try:
        start_scheduler(svc, minutes=settings.POLL_INTERVAL_MINUTES)
        print(f"Scheduler started successfully with {settings.POLL_INTERVAL_MINUTES} minute interval")
    except Exception as e:
        print(f"Failed to start scheduler: {e}")
        # Continue app startup even if scheduler fails

    return app

# For gunicorn: mediator.app:create_app()
