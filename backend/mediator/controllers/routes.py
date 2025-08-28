from flask import Blueprint, request, jsonify
from functools import wraps
from ..services.config_service import config_service
from ..services.user_service import user_service
from ..configs.settings import Settings
from ..database.db import get_db
import jwt
from datetime import datetime, timedelta

routes = Blueprint('routes', __name__)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({'message': 'Invalid token format'}), 401
        
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        
        # Get database session for this request
        db = next(get_db())
        try:
            # Get JWT secret from config service
            jwt_secret = config_service.get_config('system.jwt_secret', db)
            if not jwt_secret:
                return jsonify({'message': 'JWT secret not configured'}), 500
            
            data = jwt.decode(token, jwt_secret, algorithms=["HS256"])
            current_user = user_service.get_user_by_id(data['user_id'], db)
            
            if not current_user:
                return jsonify({'message': 'Invalid token'}), 401
            
            if not current_user.is_active:
                return jsonify({'message': 'User account is inactive'}), 401
                
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token'}), 401
        finally:
            db.close()
        
        return f(current_user, *args, **kwargs)
    
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(current_user, *args, **kwargs):
        if not current_user.is_admin:
            return jsonify({'message': 'Admin access required'}), 403
        return f(current_user, *args, **kwargs)
    return decorated

@routes.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'message': 'Fulfil ShipHero Mediator is running'})

@routes.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'message': 'Username and password are required'}), 400
    
    # Get database session for this request
    db = next(get_db())
    try:
        user = user_service.authenticate_user(username, password, db)
        if not user:
            return jsonify({'message': 'Invalid credentials'}), 401
        
        if not user.is_active:
            return jsonify({'message': 'User account is inactive'}), 401
        
        # Get JWT secret from config service
        jwt_secret = config_service.get_config('system.jwt_secret', db)
        if not jwt_secret:
            return jsonify({'message': 'JWT secret not configured'}), 500
        
        # Generate token
        token = jwt.encode({
            'user_id': user.id,
            'username': user.username,
            'is_admin': user.is_admin,
            'exp': datetime.utcnow() + timedelta(hours=24)
        }, jwt_secret, algorithm="HS256")
        
        return jsonify({
            'token': token,
            'user': user_service.to_dict(user)
        })
    finally:
        db.close()

@routes.route('/validate-token', methods=['GET'])
@token_required
def validate_token(current_user):
    return jsonify(user_service.to_dict(current_user))

@routes.route('/config', methods=['GET'])
@token_required
def get_config(current_user):
    # Get database session for this request
    db = next(get_db())
    try:
        config = config_service.get_config_for_frontend(db)
        return jsonify(config)
    except Exception as e:
        return jsonify({'message': str(e)}), 500
    finally:
        db.close()

@routes.route('/config/fulfil', methods=['PUT'])
@token_required
@admin_required
def update_fulfil_config(current_user):
    # Get database session for this request
    db = next(get_db())
    try:
        data = request.get_json()
        mode = data.get('mode', 'live').strip().lower()
        live_subdomain = data.get('live', {}).get('subdomain', '').strip()
        live_api_key = data.get('live', {}).get('apiKey', '').strip()
        test_subdomain = data.get('test', {}).get('subdomain', '').strip()
        test_api_key = data.get('test', {}).get('apiKey', '').strip()
        
        if not live_subdomain and not test_subdomain:
            return jsonify({'message': 'At least one subdomain is required'}), 400
        
        success = config_service.update_fulfil_configs(
            mode, live_subdomain, live_api_key, test_subdomain, test_api_key, db
        )
        if success:
            # Reload settings
            Settings.load_from_database(config_service)
            return jsonify({'message': 'Fulfil configuration updated successfully'})
        else:
            return jsonify({'message': 'Failed to update Fulfil configuration'}), 500
    except Exception as e:
        return jsonify({'message': str(e)}), 500
    finally:
        db.close()

@routes.route('/config/shiphero', methods=['PUT'])
@token_required
@admin_required
def update_shiphero_config(current_user):
    # Get database session for this request
    db = next(get_db())
    try:
        data = request.get_json()
        mode = data.get('mode', 'live').strip().lower()
        
        # Live configuration
        live_refresh_token = data.get('live', {}).get('refreshToken', '').strip()
        live_oauth_url = data.get('live', {}).get('oauthUrl', '').strip()
        live_api_base_url = data.get('live', {}).get('apiBaseUrl', '').strip()
        live_default_warehouse_id = (data.get('live', {}).get('defaultWarehouseId') or '').strip()
        
        # Test configuration
        test_refresh_token = data.get('test', {}).get('refreshToken', '').strip()
        test_oauth_url = data.get('test', {}).get('oauthUrl', '').strip()
        test_api_base_url = data.get('test', {}).get('apiBaseUrl', '').strip()
        test_default_warehouse_id = (data.get('test', {}).get('defaultWarehouseId') or '').strip()
        
        if not live_refresh_token and not test_refresh_token:
            return jsonify({'message': 'At least one refresh token is required'}), 400
        
        if not live_oauth_url and not test_oauth_url:
            return jsonify({'message': 'At least one OAuth URL is required'}), 400
        
        if not live_api_base_url and not test_api_base_url:
            return jsonify({'message': 'At least one API base URL is required'}), 400
        
        success = config_service.update_shiphero_configs(
            mode, live_refresh_token, live_oauth_url, live_api_base_url, live_default_warehouse_id,
            test_refresh_token, test_oauth_url, test_api_base_url, test_default_warehouse_id, db
        )
        if success:
            # Reload settings
            Settings.load_from_database(config_service)
            return jsonify({'message': 'ShipHero configuration updated successfully'})
        else:
            return jsonify({'message': 'Failed to update ShipHero configuration'}), 500
    except Exception as e:
        return jsonify({'message': str(e)}), 500
    finally:
        db.close()

@routes.route('/config/system', methods=['PUT'])
@token_required
@admin_required
def update_system_config(current_user):
    # Get database session for this request
    db = next(get_db())
    try:
        data = request.get_json()
        poll_interval = data.get('pollIntervalMinutes')
        
        if not isinstance(poll_interval, int) or poll_interval < 1 or poll_interval > 60:
            return jsonify({'message': 'Poll interval must be between 1 and 60 minutes'}), 400
        
        success = config_service.update_system_config(poll_interval, db)
        if success:
            # Reload settings
            Settings.load_from_database(config_service)
            return jsonify({'message': 'System configuration updated successfully'})
        else:
            return jsonify({'message': 'Failed to update system configuration'}), 500
    except Exception as e:
        return jsonify({'message': str(e)}), 500
    finally:
        db.close()

@routes.route('/config/email', methods=['GET'])
@token_required
@admin_required
def get_email_config(current_user):
    # Get database session for this request
    db = next(get_db())
    try:
        email_config = config_service.get_email_config(db)
        if email_config:
            return jsonify(email_config)
        return jsonify({
            'smtpHost': '',
            'smtpPort': 587,
            'smtpUsername': '',
            'smtpPassword': '',
            'smtpUseTls': True,
            'smtpUseSsl': False,
            'fromEmail': '',
            'fromName': 'Fulfil ShipHero Mediator',
            'isActive': False
        })
    except Exception as e:
        return jsonify({'message': str(e)}), 500
    finally:
        db.close()

@routes.route('/config/email', methods=['PUT'])
@token_required
@admin_required
def update_email_config(current_user):
    # Get database session for this request
    db = next(get_db())
    try:
        data = request.get_json()
        smtp_host = data.get('smtpHost', '').strip()
        smtp_port = data.get('smtpPort', 587)
        smtp_username = data.get('smtpUsername', '').strip()
        smtp_password = data.get('smtpPassword', '').strip()
        smtp_use_tls = data.get('smtpUseTls', True)
        smtp_use_ssl = data.get('smtpUseSsl', False)
        from_email = data.get('fromEmail', '').strip()
        from_name = data.get('fromName', '').strip()
        
        if not smtp_host:
            return jsonify({'message': 'SMTP host is required'}), 400
        
        if not smtp_username:
            return jsonify({'message': 'SMTP username is required'}), 400
        
        if not smtp_password:
            return jsonify({'message': 'SMTP password is required'}), 400
        
        if not isinstance(smtp_port, int) or smtp_port < 1 or smtp_port > 65535:
            return jsonify({'message': 'SMTP port must be between 1 and 65535'}), 400
        
        success = config_service.update_email_config(
            smtp_host=smtp_host,
            smtp_port=smtp_port,
            smtp_username=smtp_username,
            smtp_password=smtp_password,
            smtp_use_tls=smtp_use_tls,
            smtp_use_ssl=smtp_use_ssl,
            from_email=from_email,
            from_name=from_name,
            db=db
        )
        
        if success:
            return jsonify({'message': 'Email configuration updated successfully'})
        else:
            return jsonify({'message': 'Failed to update email configuration'}), 500
    except Exception as e:
        return jsonify({'message': str(e)}), 500
    finally:
        db.close()

@routes.route('/config/email/test', methods=['POST'])
@token_required
@admin_required
def test_email_config(current_user):
    # Get database session for this request
    db = next(get_db())
    try:
        result = config_service.test_email_config(db)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        db.close()

@routes.route('/users', methods=['GET'])
@token_required
@admin_required
def get_users(current_user):
    # Get database session for this request
    db = next(get_db())
    try:
        users = user_service.get_all_users(db)
        return jsonify([user_service.to_dict(user) for user in users])
    except Exception as e:
        return jsonify({'message': str(e)}), 500
    finally:
        db.close()

@routes.route('/users', methods=['POST'])
@token_required
@admin_required
def create_user(current_user):
    # Get database session for this request
    db = next(get_db())
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        is_admin = data.get('isAdmin', False)
        
        if not username or not email or not password:
            return jsonify({'message': 'Username, email, and password are required'}), 400
        
        if len(password) < 6:
            return jsonify({'message': 'Password must be at least 6 characters long'}), 400
        
        # Check if user already exists
        existing_user = user_service.get_user_by_username(username, db)
        if existing_user:
            return jsonify({'message': 'Username already exists'}), 400
        
        existing_email = user_service.get_user_by_email(email, db)
        if existing_email:
            return jsonify({'message': 'Email already exists'}), 400
        
        # Create user
        new_user = user_service.create_user(username, email, password, is_admin, db)
        if new_user:
            return jsonify({
                'message': 'User created successfully',
                'user': user_service.to_dict(new_user)
            })
        else:
            return jsonify({'message': 'Failed to create user'}), 500
    except Exception as e:
        return jsonify({'message': str(e)}), 500
    finally:
        db.close()

@routes.route('/product-sync/status', methods=['GET'])
@token_required
def get_product_sync_status(current_user):
    """Get the current product synchronization status"""
    try:
        from ..services.product_sync_service import product_sync_service
        service = product_sync_service
        status = service.get_sync_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({'message': f'Failed to get product sync status: {str(e)}'}), 500

@routes.route('/product-sync/logs', methods=['GET'])
@token_required
def get_product_sync_logs(current_user):
    """Get paginated product synchronization logs"""
    from ..database.db import get_db
    from ..models.models import ProductSyncLog, Product
    from sqlalchemy import or_, cast
    from sqlalchemy.types import String
    db = next(get_db())
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        if per_page > 100:
            per_page = 100
        offset = (page - 1) * per_page
        q = (request.args.get('q') or '').strip()
        mode = (request.args.get('mode') or '').strip().lower()
        
        # If no mode specified, use the current configured sync mode
        if mode not in ('live', 'test'):
            mode = config_service.get_sync_mode(db)

        base_query = db.query(ProductSyncLog).join(Product, ProductSyncLog.product_id == Product.id, isouter=True)
        base_query = base_query.filter(ProductSyncLog.mode == mode)

        if q:
            # Determine if q is numeric (possible fulfil_id)
            is_numeric = q.isdigit()
            like_q = f"%{q}%"
            filters = [
                ProductSyncLog.product_name.ilike(like_q),
                ProductSyncLog.product_code.ilike(like_q),
            ]
            if is_numeric:
                # Match fulfil_id exactly
                filters.append(Product.fulfil_id == int(q))
            # Also allow searching shiphero_id loosely
            filters.append(cast(Product.shiphero_id, String).ilike(like_q))
            base_query = base_query.filter(or_(*filters))
        
        total = base_query.count()
        logs = base_query.order_by(ProductSyncLog.synced_at.desc()).offset(offset).limit(per_page).all()
        
        def serialize(log):
            return {
                'id': log.id,
                'product_code': log.product_code,
                'product_name': log.product_name,
                'action': log.action,
                'changed_fields': log.changed_fields,
                'synced_at': log.synced_at.isoformat() if log.synced_at else None,
                'mode': log.mode,
            }
        
        return jsonify({
            'items': [serialize(l) for l in logs],
            'page': page,
            'per_page': per_page,
            'total': total,
            'total_pages': (total + per_page - 1) // per_page,
            'current_mode': mode  # Include current mode in response
        })
    except Exception as e:
        return jsonify({'message': f'Failed to get product sync logs: {str(e)}'}), 500
    finally:
        db.close()

# Backward compatible endpoints (optional): keep existing ones if used by frontend
@routes.route('/sync/status', methods=['GET'])
@token_required
def get_sync_status(current_user):
    return get_product_sync_status(current_user)

@routes.route('/sync/logs', methods=['GET'])
@token_required
def get_sync_logs(current_user):
    return get_product_sync_logs(current_user)

@routes.route('/config/product-sync/mode', methods=['GET'])
@token_required
def get_product_sync_mode(current_user):
    # Get database session for this request
    db = next(get_db())
    try:
        mode = config_service.get_config('product_sync.mode', db) or 'live'
        return jsonify({'mode': mode})
    except Exception as e:
        return jsonify({'message': str(e)}), 500
    finally:
        db.close()

@routes.route('/config/product-sync/mode', methods=['PUT'])
@token_required
@admin_required
def update_product_sync_mode(current_user):
    # Get database session for this request
    db = next(get_db())
    try:
        data = request.get_json()
        mode = data.get('mode', 'live').strip().lower()
        
        if mode not in ['live', 'test']:
            return jsonify({'message': 'Mode must be either "live" or "test"'}), 400
        
        success = config_service.set_config('product_sync.mode', mode, 'Active module mode for product sync (live/test)', False, db)
        if success:
            # Reload settings
            Settings.load_from_database(config_service)
            
            # Reload the product sync service configuration to use the new mode
            from ..services.product_sync_service import product_sync_service
            product_sync_service.reload_configuration()
            
            return jsonify({'message': 'Product sync mode updated successfully'})
        else:
            return jsonify({'message': 'Failed to update product sync mode'}), 500
    except Exception as e:
        return jsonify({'message': str(e)}), 500
    finally:
        db.close()

@routes.route('/product-sync/check', methods=['GET'])
@token_required
def product_sync_check(current_user):
    """Check a product's presence and data across DB, Fulfil, and ShipHero based on mode."""
    from ..database.db import get_db
    from ..models.models import Product
    db = next(get_db())
    try:
        code = (request.args.get('code') or '').strip()
        mode = (request.args.get('mode') or '').strip().lower()
        if not code:
            return jsonify({'message': 'code is required'}), 400
        if mode not in ('live', 'test'):
            mode = config_service.get_sync_mode()

        # Look up in our DB first (per mode)
        product = db.query(Product).filter(Product.mode == mode, Product.code == code).first()
        db_fulfil_id = product.fulfil_id if product else None
        db_shiphero_id = product.shiphero_id if product else None

        # Serialize local product fields for comparison
        def to_serializable(val):
            try:
                from decimal import Decimal
                if isinstance(val, Decimal):
                    return float(val)
            except Exception:
                pass
            return val

        local_fields = None
        if product:
            local_fields = {
                'mode': product.mode,
                'fulfil_id': product.fulfil_id,
                'shiphero_id': product.shiphero_id,
                'code': product.code,
                'name': product.name,
                'template_name': product.template_name,
                'category_name': product.category_name,
                'variant_name': product.variant_name,
                'upc': product.upc,
                'asin': product.asin,
                'buyer_sku': product.buyer_sku,
                'weight_gm': to_serializable(product.weight_gm),
                'weight_oz': to_serializable(product.weight_oz),
                'length_cm': to_serializable(product.length_cm),
                'width_cm': to_serializable(product.width_cm),
                'height_cm': to_serializable(product.height_cm),
                'length_in': to_serializable(product.length_in),
                'width_in': to_serializable(product.width_in),
                'height_in': to_serializable(product.height_in),
                'dimension_unit': product.dimension_unit,
                'weight_uom': product.weight_uom,
                'country_of_origin': product.country_of_origin,
                'hs_code': product.hs_code,
                'customs_description': product.customs_description,
                'quantity_per_case': product.quantity_per_case,
                'unit_of_measure': product.unit_of_measure,
                'image_url': product.image_url,
            }

        # Initialize external services for the requested mode
        fulfil_cfg = config_service.get_fulfil_config_for_mode(mode)
        shiphero_cfg = config_service.get_shiphero_config_for_mode(mode)

        fulfil_data = None
        fulfil_normalized = None
        shiphero_data = None
        fulfil_error = None
        shiphero_error = None

        # Fulfil fetch: by code through paging (Fulfil API docs: products.json)
        try:
            if fulfil_cfg.get('subdomain') and fulfil_cfg.get('api_key'):
                from mediator.services.fulfil_service import FulfilService
                fs = FulfilService(
                    fulfil_cfg['subdomain'], fulfil_cfg['api_key']
                )
                fulfil_data = fs.get_product_by_code(code)
                if fulfil_data:
                    try:
                        fulfil_normalized = fs.parse_product_data(fulfil_data)
                    except Exception:
                        fulfil_normalized = None
            else:
                fulfil_error = 'Fulfil configuration not set for this mode'
        except Exception as e:
            fulfil_error = str(e)

        # ShipHero fetch: prefer by SKU; if DB has id, we can try by id
        try:
            if shiphero_cfg.get('refresh_token') and shiphero_cfg.get('oauth_url') and shiphero_cfg.get('api_base_url'):
                from mediator.services.shiphero_service import ShipHeroService
                sh = ShipHeroService(
                    shiphero_cfg['refresh_token'], shiphero_cfg['oauth_url'], shiphero_cfg['api_base_url']
                )
                if db_shiphero_id:
                    shiphero_data = sh.get_product_by_id(db_shiphero_id)
                if not shiphero_data:
                    shiphero_data = sh.get_product_by_sku(code)
            else:
                shiphero_error = 'ShipHero configuration not set for this mode'
        except Exception as e:
            shiphero_error = str(e)

        # Normalize ShipHero to local fields for comparison
        shiphero_normalized = None
        if shiphero_data:
            try:
                dims = (shiphero_data.get('dimensions') or {}) if isinstance(shiphero_data, dict) else {}
                shiphero_normalized = {
                    'code': shiphero_data.get('sku'),
                    'name': shiphero_data.get('name'),
                    'upc': shiphero_data.get('barcode'),
                    'hs_code': shiphero_data.get('tariff_code'),
                    'customs_description': shiphero_data.get('customs_description'),
                    'country_of_origin': shiphero_data.get('country_of_manufacture'),
                    # Dimensions as provided by ShipHero (strings). Units depend on account; display only
                    'length_cm': None,
                    'width_cm': None,
                    'height_cm': None,
                    'length_in': dims.get('length'),
                    'width_in': dims.get('width'),
                    'height_in': dims.get('height'),
                    'weight_gm': None,
                    'weight_oz': dims.get('weight'),
                    'image_url': None,
                    'template_name': None,
                    'category_name': None,
                    'variant_name': None,
                    'asin': None,
                    'buyer_sku': None,
                    'quantity_per_case': None,
                    'unit_of_measure': None,
                    'dimension_unit': None,
                    'weight_uom': None,
                }
            except Exception:
                shiphero_normalized = None

        return jsonify({
            'mode': mode,
            'code': code,
            'database': {
                'exists': product is not None,
                'fulfil_id': db_fulfil_id,
                'shiphero_id': db_shiphero_id,
            },
            'local': local_fields,
            'fulfil': {
                'success': fulfil_data is not None,
                'error': fulfil_error,
                'data': fulfil_data,
                'normalized': fulfil_normalized,
                'docs': 'https://fulfil-3pl-integration-api.readme.io/reference/list-all-products'
            },
            'shiphero': {
                'success': shiphero_data is not None,
                'error': shiphero_error,
                'data': shiphero_data,
                'normalized': shiphero_normalized,
                'docs': 'https://developer.shiphero.com/examples-query/#product'
            }
        })
    except Exception as e:
        return jsonify({'message': f'Failed to check product sync: {str(e)}'}), 500
    finally:
        db.close()
