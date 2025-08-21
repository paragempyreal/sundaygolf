#!/usr/bin/env python3
"""
Utility script to initialize ShipHero tokens in the database.
Run this after setting up your environment variables and before starting the main service.
"""

import os
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from mediator.database.db import SessionLocal, engine
from mediator.models.models import Base, ShipHeroToken

def init_database():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
    print("Database tables created/verified")

def init_shiphero_token():
    """Initialize ShipHero token in database"""
    load_dotenv()
    
    # Get token from environment variables
    access_token = os.getenv("SHIPHERO_ACCESS_TOKEN")
    refresh_token = os.getenv("SHIPHERO_REFRESH_TOKEN")
    
    if not access_token or not refresh_token:
        print("Error: SHIPHERO_ACCESS_TOKEN and SHIPHERO_REFRESH_TOKEN must be set in .env file")
        return False
    
    # Set expiration (default to 1 hour from now)
    expires_in = int(os.getenv("SHIPHERO_TOKEN_EXPIRES_IN", "3600"))
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
    
    db = SessionLocal()
    try:
        # Check if token already exists
        existing = db.query(ShipHeroToken).first()
        if existing:
            print(f"Token already exists in database (ID: {existing.id})")
            return True
        
        # Create new token
        token = ShipHeroToken(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at
        )
        db.add(token)
        db.commit()
        db.refresh(token)
        
        print(f"ShipHero token initialized successfully (ID: {token.id})")
        print(f"Access token expires at: {expires_at}")
        return True
        
    except Exception as e:
        print(f"Error initializing token: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def main():
    """Main function"""
    print("Initializing Fulfil-ShipHero Mediator Database...")
    
    try:
        # Initialize database tables
        init_database()
        
        # Initialize ShipHero token
        if init_shiphero_token():
            print("\n✅ Database initialization completed successfully!")
            print("\nYou can now start the main service with:")
            print("  docker compose up --build")
            print("  or")
            print("  FLASK_APP=mediator.app:app flask run --port 8000")
        else:
            print("\n❌ Database initialization failed!")
            return 1
            
    except Exception as e:
        print(f"\n❌ Error during initialization: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
