from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from ..models.models import User
from ..database.db import get_db
import bcrypt
import secrets

class UserService:
    """Service for managing users and authentication"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verify a password against its hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    @staticmethod
    def create_user(username: str, email: str, password: str, is_admin: bool = False, db: Session = None) -> Optional[User]:
        """Create a new user"""
        if db is None:
            db = next(get_db())
        
        try:
            # Check if user already exists
            existing_user = db.query(User).filter(
                (User.username == username) | (User.email == email)
            ).first()
            
            if existing_user:
                return None
            
            # Create new user
            user = User(
                username=username,
                email=email,
                password_hash=UserService.hash_password(password),
                is_admin=is_admin
            )
            
            db.add(user)
            db.commit()
            db.refresh(user)
            
            return user
        except Exception as e:
            db.rollback()
            print(f"Error creating user: {e}")
            return None
    
    @staticmethod
    def get_user_by_username(username: str, db: Session = None) -> Optional[User]:
        """Get user by username"""
        if db is None:
            db = next(get_db())
        
        return db.query(User).filter(User.username == username).first()
    
    @staticmethod
    def get_user_by_id(user_id: int, db: Session = None) -> Optional[User]:
        """Get user by ID"""
        if db is None:
            db = next(get_db())
        
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def authenticate_user(username: str, password: str, db: Session = None) -> Optional[User]:
        """Authenticate a user with username and password"""
        if db is None:
            db = next(get_db())
        
        user = UserService.get_user_by_username(username, db)
        if user and UserService.verify_password(password, user.password_hash):
            return user
        return None
    
    @staticmethod
    def update_user(user_id: int, updates: Dict[str, Any], db: Session = None) -> bool:
        """Update user information"""
        if db is None:
            db = next(get_db())
        
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return False
            
            # Update allowed fields
            if 'email' in updates:
                user.email = updates['email']
            if 'is_active' in updates:
                user.is_active = updates['is_active']
            if 'is_admin' in updates:
                user.is_admin = updates['is_admin']
            
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            print(f"Error updating user: {e}")
            return False
    
    @staticmethod
    def change_password(user_id: int, new_password: str, db: Session = None) -> bool:
        """Change user password"""
        if db is None:
            db = next(get_db())
        
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return False
            
            user.password_hash = UserService.hash_password(new_password)
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            print(f"Error changing password: {e}")
            return False
    
    @staticmethod
    def delete_user(user_id: int, db: Session = None) -> bool:
        """Delete a user"""
        if db is None:
            db = next(get_db())
        
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return False
            
            db.delete(user)
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            print(f"Error deleting user: {e}")
            return False
    
    @staticmethod
    def get_all_users(db: Session = None) -> list[User]:
        """Get all users"""
        if db is None:
            db = next(get_db())
        
        return db.query(User).all()
    
    @staticmethod
    def initialize_default_admin(db: Session = None) -> bool:
        """Initialize default admin user if no users exist"""
        if db is None:
            db = next(get_db())
        
        try:
            # Check if any users exist
            existing_users = db.query(User).count()
            if existing_users > 0:
                return True  # Users already exist
            
            # Create default admin user
            admin_user = UserService.create_user(
                username='sundaygolfadmin',
                email='admin@sundaygolf.com',
                password='sundaygolf@123',
                is_admin=True,
                db=db
            )
            
            return admin_user is not None
        except Exception as e:
            print(f"Error initializing default admin: {e}")
            return False
    
    @staticmethod
    def to_dict(user: User) -> Dict[str, Any]:
        """Convert user object to dictionary"""
        return {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'is_active': user.is_active,
            'is_admin': user.is_admin,
            'created_at': user.created_at.isoformat() if user.created_at else None,
            'updated_at': user.updated_at.isoformat() if user.updated_at else None
        }

# Global instance
user_service = UserService()
