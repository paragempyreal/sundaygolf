from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from mediator.configs.settings import settings

# Configure database engine with proper connection pool settings
engine = create_engine(
    settings.DATABASE_URL, 
    pool_pre_ping=True,
    pool_size=10,  # Increase pool size
    max_overflow=20,  # Increase max overflow
    pool_timeout=60,  # Increase timeout
    pool_recycle=3600,  # Recycle connections after 1 hour
    echo=False  # Set to True for debugging SQL queries
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_db_session():
    """Get a single database session (use with caution)"""
    return SessionLocal()
