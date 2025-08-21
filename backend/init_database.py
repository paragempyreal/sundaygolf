#!/usr/bin/env python3
"""
Database initialization script for Fulfil ShipHero Mediator
This script creates the necessary tables and initializes default data
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mediator.database.db import engine, SessionLocal
from mediator.models.models import Base
from mediator.services.config_service import config_service
from mediator.services.user_service import user_service
from mediator.configs.settings import settings

def init_database():
    """Initialize the database with all tables and default data"""
    print("🚀 Initializing Fulfil ShipHero Mediator Database...")
    
    try:
        # Create all tables
        print("📋 Creating database tables...")
        Base.metadata.create_all(bind=engine)
        print("✅ Tables created successfully")
        
        # Initialize database session
        db = SessionLocal()
        
        try:
            # Initialize default configuration
            print("⚙️  Initializing default configuration...")
            config_service.initialize_default_config(db)
            print("✅ Default configuration initialized")
            
            # Ensure secret keys are set
            print("🔑 Ensuring secret keys...")
            config_service.ensure_secret_keys(db)
            print("✅ Secret keys ensured")
            
            # Initialize default admin user
            print("👤 Creating default admin user...")
            user_service.initialize_default_admin(db)
            print("✅ Default admin user created")
            
            # Load configuration into settings
            print("🔄 Loading configuration...")
            settings.load_from_database(config_service)
            print("✅ Configuration loaded")
            
            print("\n🎉 Database initialization completed successfully!")
            print("\n📋 Default credentials:")
            print("   Username: admin")
            print("   Password: admin123")
            print("\n⚠️  IMPORTANT: Change the default password in production!")
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        sys.exit(1)

def reset_database():
    """Reset the database (drop all tables and recreate)"""
    print("⚠️  WARNING: This will delete all data!")
    response = input("Are you sure you want to continue? (yes/no): ")
    
    if response.lower() != 'yes':
        print("Operation cancelled.")
        return
    
    try:
        print("🗑️  Dropping all tables...")
        Base.metadata.drop_all(bind=engine)
        print("✅ Tables dropped")
        
        # Reinitialize
        init_database()
        
    except Exception as e:
        print(f"❌ Error resetting database: {e}")
        sys.exit(1)

def show_status():
    """Show current database status"""
    print("📊 Database Status:")
    
    try:
        db = SessionLocal()
        
        try:
            # Count configurations
            config_count = db.query(config_service.__class__).count()
            print(f"   Configurations: {config_count}")
            
            # Count users
            user_count = db.query(user_service.__class__).count()
            print(f"   Users: {user_count}")
            
            # Show some config values
            print("\n🔧 Current Configuration:")
            configs = config_service.get_all_config(db)
            for key, value in configs.items():
                if configs.get(key, {}).get('is_sensitive', False):
                    display_value = '***' if value else '(not set)'
                else:
                    display_value = value or '(not set)'
                print(f"   {key}: {display_value}")
                
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Error checking status: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "reset":
            reset_database()
        elif command == "status":
            show_status()
        elif command == "help":
            print("Available commands:")
            print("  python init_database.py          - Initialize database")
            print("  python init_database.py reset    - Reset database (drop all data)")
            print("  python init_database.py status   - Show database status")
            print("  python init_database.py help     - Show this help")
        else:
            print(f"Unknown command: {command}")
            print("Use 'python init_database.py help' for available commands")
    else:
        init_database()
