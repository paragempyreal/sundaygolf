from flask import Flask
from sqlalchemy import text
from mediator.configs.settings import settings
from mediator.database.db import engine, SessionLocal
from mediator.controllers.routes import routes
from mediator.models.models import Base
from mediator.services.config_service import config_service
from mediator.services.user_service import user_service
from datetime import datetime

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
    CORS(app, origins=settings.CORS_ORIGINS.split(','), supports_credentials=True)
    
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

    # Set up background sync task
    from .services.product_sync_service import product_sync_service
    import threading
    import time
    
    def periodic_sync():
        """Periodically sync products"""
        while True:
            try:
                # Re-read latest poll interval from DB each cycle so changes apply without restart
                try:
                    settings.load_from_database(config_service)
                except Exception as reload_err:
                    print(f"Warning: could not reload settings from DB: {reload_err}")
                interval_minutes = max(1, int(settings.POLL_INTERVAL_MINUTES or 5))
                time.sleep(interval_minutes * 60)  # Convert minutes to seconds
                print(f"Starting periodic product sync at {datetime.now()}")
                
                # Perform actual sync
                try:
                    result = product_sync_service.sync_all_products()
                    print(f"Periodic sync completed successfully: {result}")
                except Exception as sync_error:
                    print(f"Error during periodic sync: {sync_error}")
            except Exception as e:
                print(f"Error in periodic sync: {e}")
    
    # Start background sync thread
    sync_thread = threading.Thread(target=periodic_sync, daemon=True)
    sync_thread.start()
    print("Background sync thread started")

    # Run the app on the specified port
    app.run(port=int(settings.APP_PORT))

    return app
# For gunicorn: mediator.app:create_app()
