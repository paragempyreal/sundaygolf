from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from ..models.models import Configuration
from ..database.db import get_db
import hashlib
import os

class ConfigService:
    """Service for managing configuration stored in database"""
    
    # Default configuration keys
    DEFAULT_CONFIG = {
        # Fulfil configs (test/live + mode)
        'fulfil.live_subdomain': {'value': '', 'description': 'Fulfil live subdomain', 'is_sensitive': False},
        'fulfil.live_api_key': {'value': '', 'description': 'Fulfil live API key', 'is_sensitive': False},
        'fulfil.test_subdomain': {'value': '', 'description': 'Fulfil test subdomain', 'is_sensitive': False},
        'fulfil.test_api_key': {'value': '', 'description': 'Fulfil test API key', 'is_sensitive': False},
        
        # ShipHero configs (test/live + mode)
        'shiphero.live_refresh_token': {'value': '', 'description': 'ShipHero live OAuth refresh token', 'is_sensitive': False},
        'shiphero.live_oauth_url': {'value': 'https://public-api.shiphero.com/auth/refresh', 'description': 'ShipHero live OAuth URL', 'is_sensitive': False},
        'shiphero.live_api_base_url': {'value': 'https://public-api.shiphero.com', 'description': 'ShipHero live API base URL', 'is_sensitive': False},
        'shiphero.live_default_warehouse_id': {'value': '', 'description': 'ShipHero live default warehouse id', 'is_sensitive': False},
        'shiphero.test_refresh_token': {'value': '', 'description': 'ShipHero test OAuth refresh token', 'is_sensitive': False},
        'shiphero.test_oauth_url': {'value': 'https://public-api.shiphero.com/auth/refresh', 'description': 'ShipHero test OAuth URL', 'is_sensitive': False},
        'shiphero.test_api_base_url': {'value': 'https://public-api.shiphero.com', 'description': 'ShipHero test API base URL', 'is_sensitive': False},
        'shiphero.test_default_warehouse_id': {'value': '', 'description': 'ShipHero test default warehouse id', 'is_sensitive': False},
        
        # Product Sync module mode
        'product_sync.mode': {'value': 'live', 'description': 'Active module mode for product sync (live/test)', 'is_sensitive': False},
        
        # System
        'system.poll_interval_minutes': {'value': '1', 'description': 'Sync poll interval in minutes', 'is_sensitive': False},
        'system.secret_key': {'value': '', 'description': 'Application secret key', 'is_sensitive': False},
        'system.jwt_secret': {'value': '', 'description': 'JWT signing secret', 'is_sensitive': False},
        
        # Email
        'email.smtp_host': {'value': '', 'description': 'SMTP host', 'is_sensitive': False},
        'email.smtp_port': {'value': '587', 'description': 'SMTP port', 'is_sensitive': False},
        'email.smtp_username': {'value': '', 'description': 'SMTP username', 'is_sensitive': False},
        'email.smtp_password': {'value': '', 'description': 'SMTP password', 'is_sensitive': False},
        'email.smtp_use_tls': {'value': 'true', 'description': 'Use TLS', 'is_sensitive': False},
        'email.smtp_use_ssl': {'value': 'false', 'description': 'Use SSL', 'is_sensitive': False},
        'email.from_email': {'value': '', 'description': 'From email address', 'is_sensitive': False},
        'email.from_name': {'value': 'Fulfil ShipHero Mediator', 'description': 'From display name', 'is_sensitive': False},
        'email.is_active': {'value': 'false', 'description': 'Email configuration active', 'is_sensitive': False},
    }
    
    @staticmethod
    def get_sync_mode(db: Session = None) -> str:
        if db is None:
            db = next(get_db())
        return (ConfigService.get_config('product_sync.mode', db) or 'live').lower()

    @staticmethod
    def set_sync_mode(mode: str, db: Session = None) -> bool:
        return ConfigService.set_config('product_sync.mode', (mode or 'live').lower(), 'Active module mode for product sync (live/test)', False, db)

    @staticmethod
    def get_fulfil_config_for_mode(mode: str, db: Session = None) -> Dict[str, str]:
        """Get Fulfil configuration for the specified mode ('live' or 'test') with legacy fallback"""
        if db is None:
            db = next(get_db())
        effective_mode = (mode or 'live').lower()
        if effective_mode == 'test':
            subdomain = ConfigService.get_config('fulfil.test_subdomain', db) or ''
            api_key = ConfigService.get_config('fulfil.test_api_key', db) or ''
        else:
            subdomain = ConfigService.get_config('fulfil.live_subdomain', db) or ''
            api_key = ConfigService.get_config('fulfil.live_api_key', db) or ''
        # Fallback to legacy
        if not subdomain:
            subdomain = ConfigService.get_config('fulfil.subdomain', db) or ''
        if not api_key:
            api_key = ConfigService.get_config('fulfil.api_key', db) or ''
        return {
            'mode': 'test' if effective_mode == 'test' else 'live',
            'subdomain': subdomain,
            'api_key': api_key
        }

    @staticmethod
    def get_shiphero_config_for_mode(mode: str, db: Session = None) -> Dict[str, str]:
        """Get ShipHero configuration for the specified mode ('live' or 'test') with legacy fallback"""
        if db is None:
            db = next(get_db())
        effective_mode = (mode or 'live').lower()
        if effective_mode == 'test':
            refresh_token = ConfigService.get_config('shiphero.test_refresh_token', db) or ''
            oauth_url = ConfigService.get_config('shiphero.test_oauth_url', db) or 'https://public-api.shiphero.com/auth/refresh'
            api_base_url = ConfigService.get_config('shiphero.test_api_base_url', db) or 'https://public-api.shiphero.com'
            default_wh = ConfigService.get_config('shiphero.test_default_warehouse_id', db) or ''
        else:
            refresh_token = ConfigService.get_config('shiphero.live_refresh_token', db) or ''
            oauth_url = ConfigService.get_config('shiphero.live_oauth_url', db) or (ConfigService.get_config('shiphero.oauth_url', db) or 'https://public-api.shiphero.com/auth/refresh')
            api_base_url = ConfigService.get_config('shiphero.live_api_base_url', db) or (ConfigService.get_config('shiphero.api_base_url', db) or 'https://public-api.shiphero.com')
            default_wh = ConfigService.get_config('shiphero.live_default_warehouse_id', db) or (ConfigService.get_config('shiphero.default_warehouse_id', db) or '')
        # Fallback to legacy refresh token
        if not refresh_token:
            refresh_token = ConfigService.get_config('shiphero.refresh_token', db) or ''
        return {
            'mode': 'test' if effective_mode == 'test' else 'live',
            'refresh_token': refresh_token,
            'oauth_url': oauth_url,
            'api_base_url': api_base_url,
            'default_warehouse_id': default_wh
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
                if description is not None:
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
        
        # Determine modes
        fulfil_mode = (ConfigService.get_config('fulfil.mode', db) or 'live').lower()
        shiphero_mode = (ConfigService.get_config('shiphero.mode', db) or 'live').lower()
        
        # Build Fulfil payload
        fulfil_live_subdomain = ConfigService.get_config('fulfil.live_subdomain', db) or ''
        fulfil_live_api_key = ConfigService.get_config('fulfil.live_api_key', db) or ''
        fulfil_test_subdomain = ConfigService.get_config('fulfil.test_subdomain', db) or ''
        fulfil_test_api_key = ConfigService.get_config('fulfil.test_api_key', db) or ''
        
        # Backward compatibility: fall back to legacy keys if new ones empty
        legacy_sub = ConfigService.get_config('fulfil.subdomain', db) or ''
        legacy_key = ConfigService.get_config('fulfil.api_key', db) or ''
        if not fulfil_live_subdomain and legacy_sub:
            fulfil_live_subdomain = legacy_sub
        if not fulfil_live_api_key and legacy_key:
            fulfil_live_api_key = legacy_key
        
        fulfil_payload = {
            'mode': 'test' if fulfil_mode == 'test' else 'live',
            'live': {
                'subdomain': fulfil_live_subdomain,
                'apiKey': fulfil_live_api_key
            },
            'test': {
                'subdomain': fulfil_test_subdomain,
                'apiKey': fulfil_test_api_key
            }
        }
        
        # Build ShipHero payload
        live_refresh = ConfigService.get_config('shiphero.live_refresh_token', db) or ''
        live_oauth_url = ConfigService.get_config('shiphero.live_oauth_url', db) or (ConfigService.get_config('shiphero.oauth_url', db) or 'https://public-api.shiphero.com/auth/refresh')
        live_api_base = ConfigService.get_config('shiphero.live_api_base_url', db) or (ConfigService.get_config('shiphero.api_base_url', db) or 'https://public-api.shiphero.com')
        live_wh = ConfigService.get_config('shiphero.live_default_warehouse_id', db) or (ConfigService.get_config('shiphero.default_warehouse_id', db) or '')
        test_refresh = ConfigService.get_config('shiphero.test_refresh_token', db) or ''
        test_oauth_url = ConfigService.get_config('shiphero.test_oauth_url', db) or 'https://public-api.shiphero.com/auth/refresh'
        test_api_base = ConfigService.get_config('shiphero.test_api_base_url', db) or 'https://public-api.shiphero.com'
        test_wh = ConfigService.get_config('shiphero.test_default_warehouse_id', db) or ''
        
        # Backward compatibility for refresh token
        legacy_refresh = ConfigService.get_config('shiphero.refresh_token', db) or ''
        if not live_refresh and legacy_refresh:
            live_refresh = legacy_refresh
        
        shiphero_payload = {
            'mode': 'test' if shiphero_mode == 'test' else 'live',
            'live': {
                'refreshToken': live_refresh,
                'oauthUrl': live_oauth_url,
                'apiBaseUrl': live_api_base,
                'defaultWarehouseId': live_wh
            },
            'test': {
                'refreshToken': test_refresh,
                'oauthUrl': test_oauth_url,
                'apiBaseUrl': test_api_base,
                'defaultWarehouseId': test_wh
            }
        }
        
        # System
        poll_interval = int(ConfigService.get_config('system.poll_interval_minutes', db) or 5)
        
        return {
            'fulfil': fulfil_payload,
            'shiphero': shiphero_payload,
            'system': {'pollIntervalMinutes': poll_interval}
        }
    
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
        """Update Fulfil configuration (legacy method)"""
        success1 = ConfigService.set_config('fulfil.subdomain', subdomain, 'Fulfil instance subdomain (legacy)', False, db)
        success2 = ConfigService.set_config('fulfil.api_key', api_key, 'Fulfil API key (legacy)', True, db)
        return success1 and success2
    
    @staticmethod
    def update_fulfil_configs(mode: str, live_subdomain: str, live_api_key: str, test_subdomain: str, test_api_key: str, db: Session = None) -> bool:
        """Update Fulfil configuration (test/live + mode)"""
        ok = True
        ok &= ConfigService.set_config('fulfil.mode', (mode or 'live').lower(), 'Active Fulfil mode (live/test)', False, db)
        ok &= ConfigService.set_config('fulfil.live_subdomain', live_subdomain or '', 'Fulfil live subdomain', False, db)
        # Always update API key, even if blank (to allow clearing the field)
        ok &= ConfigService.set_config('fulfil.live_api_key', live_api_key or '', 'Fulfil live API key', True, db)
        ok &= ConfigService.set_config('fulfil.test_subdomain', test_subdomain or '', 'Fulfil test subdomain', False, db)
        # Always update API key, even if blank (to allow clearing the field)
        ok &= ConfigService.set_config('fulfil.test_api_key', test_api_key or '', 'Fulfil test API key', True, db)
        return bool(ok)
    
    @staticmethod
    def update_shiphero_config(refresh_token: str, oauth_url: str, api_base_url: str, db: Session = None) -> bool:
        """Update ShipHero configuration (legacy method)"""
        success1 = ConfigService.set_config('shiphero.refresh_token', refresh_token, 'ShipHero OAuth refresh token (legacy)', True, db)
        success2 = ConfigService.set_config('shiphero.oauth_url', oauth_url, 'ShipHero OAuth URL (legacy)', False, db)
        success3 = ConfigService.set_config('shiphero.api_base_url', api_base_url, 'ShipHero API base URL (legacy)', False, db)
        return success1 and success2 and success3

    @staticmethod
    def update_shiphero_configs(
        mode: str,
        live_refresh_token: str,
        live_oauth_url: str,
        live_api_base_url: str,
        live_default_warehouse_id: str,
        test_refresh_token: str,
        test_oauth_url: str,
        test_api_base_url: str,
        test_default_warehouse_id: str,
        db: Session = None
    ) -> bool:
        """Update ShipHero configuration (test/live + mode)"""
        ok = True
        ok &= ConfigService.set_config('shiphero.mode', (mode or 'live').lower(), 'Active ShipHero mode (live/test)', False, db)
        # Live
        # Always update refresh token, even if blank (to allow clearing the field)
        ok &= ConfigService.set_config('shiphero.live_refresh_token', live_refresh_token or '', 'ShipHero live OAuth refresh token', True, db)
        ok &= ConfigService.set_config('shiphero.live_oauth_url', live_oauth_url or 'https://public-api.shiphero.com/auth/refresh', 'ShipHero live OAuth URL', False, db)
        ok &= ConfigService.set_config('shiphero.live_api_base_url', live_api_base_url or 'https://public-api.shiphero.com', 'ShipHero live API base URL', False, db)
        ok &= ConfigService.set_config('shiphero.live_default_warehouse_id', live_default_warehouse_id or '', 'ShipHero live default warehouse id', False, db)
        # Test
        # Always update refresh token, even if blank (to allow clearing the field)
        ok &= ConfigService.set_config('shiphero.test_refresh_token', test_refresh_token or '', 'ShipHero test OAuth refresh token', True, db)
        ok &= ConfigService.set_config('shiphero.test_oauth_url', test_oauth_url or 'https://public-api.shiphero.com/auth/refresh', 'ShipHero test OAuth URL', False, db)
        ok &= ConfigService.set_config('shiphero.test_api_base_url', test_api_base_url or 'https://public-api.shiphero.com', 'ShipHero test API base URL', False, db)
        ok &= ConfigService.set_config('shiphero.test_default_warehouse_id', test_default_warehouse_id or '', 'ShipHero test default warehouse id', False, db)
        return bool(ok)

    @staticmethod
    def update_shiphero_default_warehouse(default_warehouse_id: str, db: Session = None) -> bool:
        """Update ShipHero default warehouse id (legacy shared)"""
        return ConfigService.set_config('shiphero.default_warehouse_id', default_warehouse_id, 'Default ShipHero warehouse id', False, db)
    
    @staticmethod
    def update_system_config(poll_interval_minutes: int, db: Session = None) -> bool:
        """Update system configuration"""
        return ConfigService.set_config('system.poll_interval_minutes', str(poll_interval_minutes), 'Sync poll interval in minutes', False, db)
    
    @staticmethod
    def get_fulfil_config(db: Session = None) -> Dict[str, str]:
        """Get Fulfil configuration for active mode (respect sync.mode; legacy fallback)"""
        if db is None:
            db = next(get_db())
        # Prefer module sync.mode if set
        mode = ConfigService.get_sync_mode(db)
        if mode not in ('live', 'test'):
            mode = (ConfigService.get_config('fulfil.mode', db) or 'live').lower()
        if mode == 'test':
            subdomain = ConfigService.get_config('fulfil.test_subdomain', db) or ''
            api_key = ConfigService.get_config('fulfil.test_api_key', db) or ''
        else:
            subdomain = ConfigService.get_config('fulfil.live_subdomain', db) or ''
            api_key = ConfigService.get_config('fulfil.live_api_key', db) or ''
        # Fallback to legacy
        if not subdomain:
            subdomain = ConfigService.get_config('fulfil.subdomain', db) or ''
        if not api_key:
            api_key = ConfigService.get_config('fulfil.api_key', db) or ''
        return {
            'mode': 'test' if mode == 'test' else 'live',
            'subdomain': subdomain,
            'api_key': api_key
        }
    
    @staticmethod
    def get_shiphero_config(db: Session = None) -> Dict[str, str]:
        """Get ShipHero configuration for active mode (respect sync.mode; legacy fallback)"""
        if db is None:
            db = next(get_db())
        # Prefer module sync.mode if set
        mode = ConfigService.get_sync_mode(db)
        if mode not in ('live', 'test'):
            mode = (ConfigService.get_config('shiphero.mode', db) or 'live').lower()
        if mode == 'test':
            refresh_token = ConfigService.get_config('shiphero.test_refresh_token', db) or ''
            oauth_url = ConfigService.get_config('shiphero.test_oauth_url', db) or 'https://public-api.shiphero.com/auth/refresh'
            api_base_url = ConfigService.get_config('shiphero.test_api_base_url', db) or 'https://public-api.shiphero.com'
            default_wh = ConfigService.get_config('shiphero.test_default_warehouse_id', db) or ''
        else:
            refresh_token = ConfigService.get_config('shiphero.live_refresh_token', db) or ''
            oauth_url = ConfigService.get_config('shiphero.live_oauth_url', db) or (ConfigService.get_config('shiphero.oauth_url', db) or 'https://public-api.shiphero.com/auth/refresh')
            api_base_url = ConfigService.get_config('shiphero.live_api_base_url', db) or (ConfigService.get_config('shiphero.api_base_url', db) or 'https://public-api.shiphero.com')
            default_wh = ConfigService.get_config('shiphero.live_default_warehouse_id', db) or (ConfigService.get_config('shiphero.default_warehouse_id', db) or '')
        # Fallback to legacy refresh token
        if not refresh_token:
            refresh_token = ConfigService.get_config('shiphero.refresh_token', db) or ''
        return {
            'mode': 'test' if mode == 'test' else 'live',
            'refresh_token': refresh_token,
            'oauth_url': oauth_url,
            'api_base_url': api_base_url,
            'default_warehouse_id': default_wh
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
    
    # Email Configuration Methods using configuration table
    @staticmethod
    def get_email_config(db: Session = None) -> Dict[str, Any] | None:
        """Get email configuration values as a dict from configuration table"""
        if db is None:
            db = next(get_db())
        host = ConfigService.get_config('email.smtp_host', db) or ''
        username = ConfigService.get_config('email.smtp_username', db) or ''
        is_active_str = ConfigService.get_config('email.is_active', db) or 'false'
        if not host or not username:
            return None
        return {
            'smtpHost': host,
            'smtpPort': int(ConfigService.get_config('email.smtp_port', db) or '587'),
            'smtpUsername': username,
            'smtpPassword': ConfigService.get_config('email.smtp_password', db) or '',
            'smtpUseTls': (ConfigService.get_config('email.smtp_use_tls', db) or 'true').lower() == 'true',
            'smtpUseSsl': (ConfigService.get_config('email.smtp_use_ssl', db) or 'false').lower() == 'true',
            'fromEmail': ConfigService.get_config('email.from_email', db) or username,
            'fromName': ConfigService.get_config('email.from_name', db) or 'Fulfil ShipHero Mediator',
            'isActive': is_active_str.lower() == 'true'
        }

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
        """Update email configuration in configuration table"""
        try:
            ok = True
            ok &= ConfigService.set_config('email.smtp_host', smtp_host, 'SMTP host', False, db)
            ok &= ConfigService.set_config('email.smtp_port', str(smtp_port), 'SMTP port', False, db)
            ok &= ConfigService.set_config('email.smtp_username', smtp_username, 'SMTP username', False, db)
            if smtp_password:
                ok &= ConfigService.set_config('email.smtp_password', smtp_password, 'SMTP password', True, db)
            ok &= ConfigService.set_config('email.smtp_use_tls', 'true' if smtp_use_tls else 'false', 'Use TLS', False, db)
            ok &= ConfigService.set_config('email.smtp_use_ssl', 'true' if smtp_use_ssl else 'false', 'Use SSL', False, db)
            ok &= ConfigService.set_config('email.from_email', from_email or smtp_username, 'From email', False, db)
            ok &= ConfigService.set_config('email.from_name', from_name or 'Fulfil ShipHero Mediator', 'From name', False, db)
            ok &= ConfigService.set_config('email.is_active', 'true', 'Email configuration active', False, db)
            return bool(ok)
        except Exception as e:
            print(f"Error updating email config: {e}")
            return False

    @staticmethod
    def test_email_config(db: Session = None) -> Dict[str, Any]:
        """Test email configuration using current configuration table values"""
        if db is None:
            db = next(get_db())
        try:
            cfg = ConfigService.get_email_config(db)
            if not cfg:
                return {'success': False, 'message': 'No email configuration found'}

            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            msg = MIMEMultipart()
            msg['From'] = f"{cfg['fromName']} <{cfg['fromEmail']}>"
            msg['To'] = cfg['smtpUsername']
            msg['Subject'] = 'Email Configuration Test'
            body = 'This is a test email to verify your email configuration is working correctly.'
            msg.attach(MIMEText(body, 'plain'))

            if cfg['smtpUseSsl']:
                server = smtplib.SMTP_SSL(cfg['smtpHost'], cfg['smtpPort'])
            else:
                server = smtplib.SMTP(cfg['smtpHost'], cfg['smtpPort'])
                if cfg['smtpUseTls']:
                    server.starttls()
            # Fetch real password for login
            real_password = ConfigService.get_config('email.smtp_password', db) or ''
            server.login(cfg['smtpUsername'], real_password)
            server.send_message(msg)
            server.quit()
            return {'success': True, 'message': 'Test email sent successfully'}
        except Exception as e:
            return {'success': False, 'message': f'Email test failed: {str(e)}'}

config_service = ConfigService()
