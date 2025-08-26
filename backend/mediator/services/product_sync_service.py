from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from ..models.models import Product, ProductSyncLog
from ..services.fulfil_service import FulfilService
from ..services.shiphero_service import ShipHeroService
from ..services.config_service import config_service
from ..database.db import get_db_session
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import logging
import json

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add a file handler for sync logs
import os
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

file_handler = logging.FileHandler(os.path.join(log_dir, "sync.log"))
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

class ProductSyncService:
    """Service for managing product synchronization from Fulfil to mediator database and ShipHero"""
    
    def __init__(self):
        self.db_session = get_db_session()
        self.fulfil_service = None
        self.shiphero_service = None
        self._initialize_services()
    
    def _initialize_services(self) -> None:
        """Initialize Fulfil and ShipHero services with configuration"""
        try:
            # Get configuration
            fulfil_config = config_service.get_fulfil_config(self.db_session)
            shiphero_config = config_service.get_shiphero_config(self.db_session)
            
            # Initialize Fulfil service if configuration is available
            if fulfil_config.get('subdomain') and fulfil_config.get('api_key'):
                self.fulfil_service = FulfilService(
                    fulfil_config['subdomain'],
                    fulfil_config['api_key']
                )
            
            # Initialize ShipHero service if configuration is available
            if (shiphero_config.get('refresh_token') and
                shiphero_config.get('oauth_url') and
                shiphero_config.get('api_base_url')):
                self.shiphero_service = ShipHeroService(
                    shiphero_config['refresh_token'],
                    shiphero_config['oauth_url'],
                    shiphero_config['api_base_url']
                )
        except Exception as e:
            logger.error(f"Failed to initialize services: {str(e)}")
    
    def _should_perform_initial_sync(self) -> bool:
        """
        Determine if we should perform an initial sync (no products in database)
        
        Returns:
            True if initial sync is needed, False for incremental sync
        """
        product_count = self.db_session.query(Product).count()
        return product_count == 0
    
    def _get_last_sync_time(self) -> Optional[datetime]:
        """
        Get the timestamp of the last successful sync
        
        Returns:
            Last sync timestamp or None if no sync has been performed
        """
        last_synced_product = self.db_session.query(Product).filter(
            Product.last_synced_at.isnot(None)
        ).order_by(Product.last_synced_at.desc()).first()
        
        return last_synced_product.last_synced_at if last_synced_product else None
    
    def sync_all_products(self) -> Dict[str, Any]:
        """
        Smart synchronization of products from Fulfil to mediator database
        
        This method automatically determines whether to perform an initial sync
        (all products) or an incremental sync (only updated products)
        
        Returns:
            Summary of sync operation
        """
        if not self.fulfil_service:
            raise Exception("Fulfil service not properly configured")
        
        summary = {
            "sync_type": "",
            "total_products": 0,
            "created": 0,
            "updated": 0,
            "failed": 0,
            "errors": [],
            "last_sync_time": None
        }
        
        # Determine sync type
        if self._should_perform_initial_sync():
            summary["sync_type"] = "initial"
            logger.info("Performing initial sync - fetching all products from Fulfil")
            fulfil_products = self.fulfil_service.get_products_for_initial_sync()
        else:
            summary["sync_type"] = "incremental"
            last_sync_time = self._get_last_sync_time()
            if last_sync_time:
                summary["last_sync_time"] = last_sync_time.isoformat()
                logger.info(f"Performing incremental sync - fetching products updated since {last_sync_time}")
                fulfil_products = self.fulfil_service.get_products_for_incremental_sync(last_sync_time)
            else:
                # Fallback to initial sync if we have products but no sync timestamp
                logger.warning("Products exist but no sync timestamp found - performing initial sync")
                summary["sync_type"] = "initial_fallback"
                fulfil_products = self.fulfil_service.get_products_for_initial_sync()
        
        summary["total_products"] = len(fulfil_products)
        logger.info(f"Found {len(fulfil_products)} products to sync")
        
        try:
            # Process each product
            for i, fulfil_product in enumerate(fulfil_products):
                try:
                    result = self._sync_single_product(fulfil_product)
                    if result == "created":
                        summary["created"] += 1
                    elif result == "updated":
                        summary["updated"] += 1
                    
                    # Log progress every 10 products
                    if (i + 1) % 10 == 0:
                        logger.info(f"Processed {i + 1}/{len(fulfil_products)} products")
                except Exception as e:
                    summary["failed"] += 1
                    error_msg = f"Failed to sync product {fulfil_product.get('code')}: {str(e)}"
                    summary["errors"].append(error_msg)
                    logger.error(error_msg)
            
            # Log final summary
            if summary["sync_type"] == "initial":
                logger.info(f"Initial sync completed: {summary['created']} created, {summary['updated']} updated, {summary['failed']} failed")
            else:
                logger.info(f"Incremental sync completed: {summary['created']} created, {summary['updated']} updated, {summary['failed']} failed")
            
        except Exception as e:
            logger.error(f"Failed to sync products: {str(e)}")
            raise Exception(f"Failed to sync products: {str(e)}")
        
        return summary
    
    def sync_product_by_id(self, fulfil_id: int) -> Dict[str, Any]:
        """
        Synchronize a single product by Fulfil ID to mediator database
        
        Args:
            fulfil_id: Fulfil product ID
            
        Returns:
            Result of sync operation
        """
        if not self.fulfil_service:
            raise Exception("Fulfil service not properly configured")
        
        try:
            # Fetch product from Fulfil
            # Note: This assumes there's an endpoint to get a single product
            # For now, we'll fetch all and filter
            fulfil_products = self.fulfil_service.get_all_products()
            target_product = None
            
            for product in fulfil_products:
                if product.get("id") == fulfil_id:
                    target_product = product
                    break
            
            if not target_product:
                raise Exception(f"Product with ID {fulfil_id} not found in Fulfil")
            
            result = self._sync_single_product(target_product)
            
            return {
                "success": True,
                "action": result,
                "product_code": target_product.get("code")
            }
            
        except Exception as e:
            logger.error(f"Failed to sync product {fulfil_id}: {str(e)}")
            raise Exception(f"Failed to sync product {fulfil_id}: {str(e)}")
    
    def _sync_single_product(self, fulfil_product: Dict[str, Any]) -> str:
        """
        Synchronize a single product from Fulfil to mediator database and ShipHero
        
        Args:
            fulfil_product: Product data from Fulfil
            
        Returns:
            Action performed ("created", "updated", or "skipped")
        """
        # Parse Fulfil product data
        parsed_data = self.fulfil_service.parse_product_data(fulfil_product)
        
        logger.debug(f"Processing product: {parsed_data['code']} ({parsed_data['name']})")
        
        # Check if product already exists in our database
        existing_product = self.db_session.query(Product).filter(
            Product.fulfil_id == parsed_data["fulfil_id"]
        ).first()
        
        current_time = datetime.now(timezone.utc)
        
        is_new_product = False
        changed_fields: Dict[str, Dict[str, Any]] = {}
        if existing_product:
            # Detect changes
            for key, new_value in parsed_data.items():
                old_value = getattr(existing_product, key, None)
                if old_value != new_value:
                    changed_fields[key] = {"old": old_value, "new": new_value}
            # Update existing product in database
            for key, value in parsed_data.items():
                setattr(existing_product, key, value)
            existing_product.updated_at = current_time
            logger.debug(f"Updated existing product in database: {existing_product.code}")
        else:
            # Create new product in database
            existing_product = Product(**parsed_data)
            self.db_session.add(existing_product)
            is_new_product = True
            # For created products, include full snapshot as changed fields (old = null)
            for key, value in parsed_data.items():
                changed_fields[key] = {"old": None, "new": value}
            logger.debug(f"Created new product in database: {existing_product.code}")
        
        # Set last_synced_at for tracking sync status
        existing_product.last_synced_at = current_time
        
        # Ensure we have an ID for logging
        self.db_session.flush()
        
        # Write sync log entry
        try:
            # Convert Decimal objects to float for JSON serialization
            serializable_changed_fields = {}
            if changed_fields:
                for key, value_dict in changed_fields.items():
                    serializable_changed_fields[key] = {
                        'old': self._convert_decimal_to_serializable(value_dict['old']),
                        'new': self._convert_decimal_to_serializable(value_dict['new'])
                    }
            
            log_entry = ProductSyncLog(
                product_id=existing_product.id,
                product_code=existing_product.code,
                product_name=existing_product.name,
                action="created" if is_new_product else "updated",
                changed_fields=json.dumps(serializable_changed_fields) if serializable_changed_fields else None
            )
            self.db_session.add(log_entry)
        except Exception as log_error:
            logger.error(f"Failed to write sync log for {existing_product.code}: {log_error}")
        
        self.db_session.commit()

        # Sync to ShipHero if service is available
        if self.shiphero_service:
            try:
                # Convert product to ShipHero format
                shiphero_data = existing_product.to_shiphero_dict()
                
                if existing_product.shiphero_id:
                    # Update existing product in ShipHero
                    logger.info(f"Updating product in ShipHero: {existing_product.code}")
                    # Choose identifier according to schema
                    id_arg = self.shiphero_service.update_id_arg_name
                    # If schema has no explicit id arg, identifier should be SKU inside data
                    if id_arg is None:
                        identifier_value = existing_product.code
                    else:
                        identifier_value = existing_product.shiphero_id
                    if id_arg == 'sku':
                        identifier_value = existing_product.code
                    elif id_arg == 'legacy_id':
                        # Fetch to get legacy_id
                        found = self.shiphero_service.get_product_by_sku(existing_product.code)
                        if found and found.get('legacy_id'):
                            identifier_value = found['legacy_id']
                    shiphero_response = self.shiphero_service.update_product(identifier_value, shiphero_data)
                    shiphero_product = shiphero_response.get("product")
                    if shiphero_product:
                        logger.info(f"Successfully updated product in ShipHero: {shiphero_product.get('sku')}")
                    else:
                        logger.error(f"Failed to update product in ShipHero: {existing_product.code}")
                else:
                    # Check if product already exists in ShipHero by SKU
                    existing_shiphero_product = self.shiphero_service.get_product_by_sku(existing_product.code)
                    if existing_shiphero_product:
                        # Update existing product
                        logger.info(f"Found existing product in ShipHero, updating: {existing_product.code}")
                        id_arg = self.shiphero_service.update_id_arg_name
                        if id_arg is None:
                            identifier_value = existing_product.code
                        elif id_arg == 'sku':
                            identifier_value = existing_product.code
                        elif id_arg in ['id', 'product_id']:
                            identifier_value = existing_shiphero_product.get('id')
                        elif id_arg == 'legacy_id':
                            identifier_value = existing_shiphero_product.get('legacy_id')
                        else:
                            identifier_value = existing_shiphero_product.get('id')
                        shiphero_response = self.shiphero_service.update_product(identifier_value, shiphero_data)
                        shiphero_product = shiphero_response.get("product")
                        # Update shiphero_id in our database
                        existing_product.shiphero_id = (shiphero_product.get("id") if shiphero_product and shiphero_product.get("id")
                                                        else existing_shiphero_product.get("id"))
                        self.db_session.commit()
                        if shiphero_product:
                            logger.info(f"Successfully updated existing product in ShipHero: {shiphero_product.get('sku')}")
                        else:
                            logger.error(f"Failed to update existing product in ShipHero: {existing_product.code}")
                    else:
                        # Create new product in ShipHero
                        logger.info(f"Creating new product in ShipHero: {existing_product.code}")
                        shiphero_response = self.shiphero_service.create_product(shiphero_data)
                        shiphero_product = shiphero_response.get("product")
                        if shiphero_product:
                            # Update shiphero_id in our database
                            existing_product.shiphero_id = shiphero_product["id"]
                            self.db_session.commit()
                            logger.info(f"Successfully created product in ShipHero: {shiphero_product.get('sku')}")
                        else:
                            logger.error(f"Failed to create product in ShipHero: {existing_product.code}")
            except Exception as shiphero_error:
                logger.error(f"Failed to sync product to ShipHero {existing_product.code}: {str(shiphero_error)}")
                # We don't raise the exception here because we still want to consider the sync successful
                # if the database sync was successful. ShipHero sync failure is logged but doesn't stop the process.
        
        # Return based on database operation
        if existing_product.id:
            logger.info(f"Synced product to mediator database: {existing_product.code}")
            return "created" if is_new_product else "updated"
        else:
            raise Exception(f"Failed to sync product to mediator database: {existing_product.code}")
    
    def _convert_decimal_to_serializable(self, value):
        """
        Convert Decimal objects to float for JSON serialization
        
        Args:
            value: Value to convert
            
        Returns:
            Converted value that can be JSON serialized
        """
        if isinstance(value, Decimal):
            return float(value)
        elif value is None:
            return None
        else:
            return value
    
    def get_sync_status(self) -> Dict[str, Any]:
        """
        Get the current sync status
        
        Returns:
            Sync status information
        """
        total_products = self.db_session.query(Product).count()
        synced_products = self.db_session.query(Product).filter(
            Product.shiphero_id.isnot(None)
        ).count()
        
        # Get products synced in the last 24 hours
        last_24_hours = datetime.now(timezone.utc) - timedelta(hours=24)
        recent_synced_products = self.db_session.query(Product).filter(
            Product.last_synced_at >= last_24_hours
        ).count()
        
        last_synced_product = self.db_session.query(Product).filter(
            Product.last_synced_at.isnot(None)
        ).order_by(Product.last_synced_at.desc()).first()
        
        last_synced_at = last_synced_product.last_synced_at if last_synced_product else None
        
        # Determine sync type for next sync
        next_sync_type = "incremental" if total_products > 0 else "initial"
        
        return {
            "total_products": total_products,
            "synced_products": synced_products,
            "pending_sync": total_products - synced_products,
            "recent_synced_products": recent_synced_products,
            "last_synced_at": last_synced_at.isoformat() if last_synced_at else None,
            "next_sync_type": next_sync_type,
            "has_products": total_products > 0
        }

# Global instance
product_sync_service = ProductSyncService()