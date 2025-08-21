from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from ..models.models import Configuration, EmailConfiguration
from ..database.db import get_db
import hashlib
import os

class ConfigService:
    """Service for managing configuration stored in database"""
    
    # Default configuration keys
    DEFAULT_CONFIG = {
        'fulfil.subdomain': {'value': '', 'description': 'Fulfil instance subdomain', 'is_sensitive': False},
        'fulfil.api_key': {'value': '', 'description': 'Fulfil API key', 'is_sensitive': True},
        'shiphero.refresh_token': {'value': '', 'description': 'ShipHero OAuth refresh token', 'is_sensitive': True},
        'shiphero.oauth_url': {'value': 'https://public-api.shiphero.com/oauth', 'description': 'ShipHero OAuth URL', 'is_sensitive': False},
        'shiphero.api_base_url': {'value': 'https://public-api.shiphero.com', 'description': 'ShipHero API base URL', 'is_sensitive': False},
        'system.poll_interval_minutes': {'value': '5', 'description': 'Sync poll interval in minutes', 'is_sensitive': False},
        'system.secret_key': {'value': '', 'description': 'Application secret key', 'is_sensitive': True},
        'system.jwt_secret': {'value': '', 'description': 'JWT signing secret', 'is_sensitive': True},
    }
    
    @staticmethod
    def get_config(key: str, db: Session = None) -> Optional[str]:
        """Get a configuration value by key"""
        if db is None:
            db = next(get_db())
        
        config = db.query(Configuration).filter(Configuration.key == key).first()
        return config.value if config else None
    
    @staticmethod
    def set_config(key: str, value: str, description: str = None, is_sensitive: bool = False, db: Session = None) -> bool:
        """Set a configuration value"""
        if db is None:
            db = next(get_db())
        
        try:
            config = db.query(Configuration).filter(Configuration.key == key).first()
            if config:
                config.value = value
                if description:
                    config.description = description
                config.is_sensitive = is_sensitive
            else:
                config = Configuration(
                    key=key,
                    value=value,
                    description=description,
                    is_sensitive=is_sensitive
                )
                db.add(config)
            
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            print(f"Error setting config {key}: {e}")
            return False
    
    @staticmethod
    def get_all_config(db: Session = None) -> Dict[str, Any]:
        """Get all configuration values"""
        if db is None:
            db = next(get_db())
        
        configs = db.query(Configuration).all()
        result = {}
        for config in configs:
            if config.is_sensitive:
                # Mask sensitive values
                if config.key.endswith('_key') or config.key.endswith('_token') or config.key.endswith('_password'):
                    result[config.key] = '*' * 8 if config.value else ''
                else:
                    result[config.key] = config.value
            else:
                result[config.key] = config.value
        return result
    
    @staticmethod
    def get_config_for_frontend(db: Session = None) -> Dict[str, Any]:
        """Get configuration formatted for frontend consumption"""
        if db is None:
            db = next(get_db())
        
        configs = db.query(Configuration).all()
        result = {
            'fulfil': {'subdomain': '', 'apiKey': ''},
            'shiphero': {'refreshToken': '', 'oauthUrl': '', 'apiBaseUrl': ''},
            'system': {'pollIntervalMinutes': 5}
        }
        
        for config in configs:
            if config.key == 'fulfil.subdomain':
                result['fulfil']['subdomain'] = config.value
            elif config.key == 'fulfil.api_key':
                result['fulfil']['apiKey'] = '*' * 8 if config.value else ''
            elif config.key == 'shiphero.refresh_token':
                result['shiphero']['refreshToken'] = '*' * 8 if config.value else ''
            elif config.key == 'shiphero.oauth_url':
                result['shiphero']['oauthUrl'] = config.value
            elif config.key == 'shiphero.api_base_url':
                result['shiphero']['apiBaseUrl'] = config.value
            elif config.key == 'system.poll_interval_minutes':
                result['system']['pollIntervalMinutes'] = int(config.value) if config.value else 5
        
        return result
    
    @staticmethod
    def initialize_default_config(db: Session = None) -> bool:
        """Initialize default configuration values"""
        if db is None:
            db = next(get_db())
        
        try:
            for key, config_data in ConfigService.DEFAULT_CONFIG.items():
                existing = db.query(Configuration).filter(Configuration.key == key).first()
                if not existing:
                    new_config = Configuration(
                        key=key,
                        value=config_data['value'],
                        description=config_data['description'],
                        is_sensitive=config_data['is_sensitive']
                    )
                    db.add(new_config)
            
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            print(f"Error initializing default config: {e}")
            return False
    
    @staticmethod
    def update_fulfil_config(subdomain: str, api_key: str, db: Session = None) -> bool:
        """Update Fulfil configuration"""
        success1 = ConfigService.set_config('fulfil.subdomain', subdomain, 'Fulfil instance subdomain', False, db)
        success2 = ConfigService.set_config('fulfil.api_key', api_key, 'Fulfil API key', True, db)
        return success1 and success2
    
    @staticmethod
    def update_shiphero_config(refresh_token: str, oauth_url: str, api_base_url: str, db: Session = None) -> bool:
        """Update ShipHero configuration"""
        success1 = ConfigService.set_config('shiphero.refresh_token', refresh_token, 'ShipHero OAuth refresh token', True, db)
        success2 = ConfigService.set_config('shiphero.oauth_url', oauth_url, 'ShipHero OAuth URL', False, db)
        success3 = ConfigService.set_config('shiphero.api_base_url', api_base_url, 'ShipHero API base URL', False, db)
        return success1 and success2 and success3
    
    @staticmethod
    def update_system_config(poll_interval_minutes: int, db: Session = None) -> bool:
        """Update system configuration"""
        return ConfigService.set_config('system.poll_interval_minutes', str(poll_interval_minutes), 'Sync poll interval in minutes', False, db)
    
    @staticmethod
    def get_fulfil_config(db: Session = None) -> Dict[str, str]:
        """Get Fulfil configuration"""
        return {
            'subdomain': ConfigService.get_config('fulfil.subdomain', db) or '',
            'api_key': ConfigService.get_config('fulfil.api_key', db) or ''
        }
    
    @staticmethod
    def get_shiphero_config(db: Session = None) -> Dict[str, str]:
        """Get ShipHero configuration"""
        return {
            'refresh_token': ConfigService.get_config('shiphero.refresh_token', db) or '',
            'oauth_url': ConfigService.get_config('shiphero.oauth_url', db) or 'https://public-api.shiphero.com/oauth',
            'api_base_url': ConfigService.get_config('shiphero.api_base_url', db) or 'https://public-api.shiphero.com'
        }
    
    @staticmethod
    def get_system_config(db: Session = None) -> Dict[str, Any]:
        """Get system configuration"""
        return {
            'poll_interval_minutes': int(ConfigService.get_config('system.poll_interval_minutes', db) or 5)
        }
    
    @staticmethod
    def generate_secret_key() -> str:
        """Generate a secure secret key"""
        return hashlib.sha256(os.urandom(32)).hexdigest()
    
    @staticmethod
    def ensure_secret_keys(db: Session = None) -> bool:
        """Ensure secret keys are set"""
        if db is None:
            db = next(get_db())
        
        try:
            # Check if secret keys exist
            secret_key = ConfigService.get_config('system.secret_key', db)
            jwt_secret = ConfigService.get_config('system.jwt_secret', db)
            
            if not secret_key:
                new_secret = ConfigService.generate_secret_key()
                ConfigService.set_config('system.secret_key', new_secret, 'Application secret key', True, db)
            
            if not jwt_secret:
                new_jwt_secret = ConfigService.generate_secret_key()
                ConfigService.set_config('system.jwt_secret', new_jwt_secret, 'JWT signing secret', True, db)
            
            return True
        except Exception as e:
            print(f"Error ensuring secret keys: {e}")
            return False

    # Email Configuration Methods
    @staticmethod
    def get_email_config(db: Session = None) -> Optional[EmailConfiguration]:
        """Get email configuration"""
        if db is None:
            db = next(get_db())
        
        return db.query(EmailConfiguration).filter(EmailConfiguration.is_active == True).first()
    
    @staticmethod
    def update_email_config(
        smtp_host: str,
        smtp_port: int,
        smtp_username: str,
        smtp_password: str,
        smtp_use_tls: bool = True,
        smtp_use_ssl: bool = False,
        from_email: str = None,
        from_name: str = None,
        db: Session = None
    ) -> bool:
        """Update email configuration"""
        if db is None:
            db = next(get_db())
        
        try:
            # Deactivate existing config
            existing_configs = db.query(EmailConfiguration).filter(EmailConfiguration.is_active == True).all()
            for config in existing_configs:
                config.is_active = False
            
            # Create new config
            new_config = EmailConfiguration(
                smtp_host=smtp_host,
                smtp_port=smtp_port,
                smtp_username=smtp_username,
                smtp_password=smtp_password,
                smtp_use_tls=smtp_use_tls,
                smtp_use_ssl=smtp_use_ssl,
                from_email=from_email or smtp_username,
                from_name=from_name or 'Fulfil ShipHero Mediator',
                is_active=True
            )
            
            db.add(new_config)
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            print(f"Error updating email config: {e}")
            return False
    
    @staticmethod
    def test_email_config(db: Session = None) -> Dict[str, Any]:
        """Test email configuration"""
        if db is None:
            db = next(get_db())
        
        try:
            email_config = ConfigService.get_email_config(db)
            if not email_config:
                return {'success': False, 'message': 'No email configuration found'}
            
            # Import here to avoid circular imports
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            # Create test message
            msg = MIMEMultipart()
            msg['From'] = f"{email_config.from_name} <{email_config.from_email}>"
            msg['To'] = email_config.smtp_username  # Send to self for testing
            msg['Subject'] = 'Email Configuration Test'
            
            body = 'This is a test email to verify your email configuration is working correctly.'
            msg.attach(MIMEText(body, 'plain'))
            
            # Connect to SMTP server
            if email_config.smtp_use_ssl:
                server = smtplib.SMTP_SSL(email_config.smtp_host, email_config.smtp_port)
            else:
                server = smtplib.SMTP(email_config.smtp_host, email_config.smtp_port)
                if email_config.smtp_use_tls:
                    server.starttls()
            
            # Login
            server.login(email_config.smtp_username, email_config.smtp_password)
            
            # Send test email
            server.send_message(msg)
            server.quit()
            
            return {'success': True, 'message': 'Test email sent successfully'}
        except Exception as e:
            return {'success': False, 'message': f'Email test failed: {str(e)}'}

config_service = ConfigService()
