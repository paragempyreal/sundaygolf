from datetime import datetime, timezone
from sqlalchemy import select
from mediator.database.db import SessionLocal
from mediator.models.models import Product, SyncRun, SyncError, FulfilCursor
from mediator.utils.utils import sha256_json, kg_to_lb, cm_to_in
import logging

# Configure logging
logger = logging.getLogger(__name__)


class SyncService:
    def __init__(self, fulfil, shiphero):
        self.fulfil = fulfil
        self.shiphero = shiphero

    def _get_cursor(self, db):
        row = db.get(FulfilCursor, 1)
        if not row:
            row = FulfilCursor(id=1)
            db.add(row)
            db.commit()
            db.refresh(row)
        return row

    def _advance_cursor(self, db, write_ts, pid):
        cur = self._get_cursor(db)
        cur.last_write_ts = write_ts
        cur.last_id = pid
        db.commit()



    def _to_db_record(self, p: dict) -> dict:
        # validation
        if not p.get("code"):
            raise ValueError("Missing SKU 'code' from Fulfil record")
        return {
            "fulfil_product_id": p["id"],
            "sku": p["code"],
            "variant_name": p.get("variant_name"),
            "upc": p.get("upc"),
            "hs_code": p.get("hs_code"),
            "country_of_origin": (p.get("country_of_origin") or None),
            "weight_kg": p.get("weight"),
            "length_cm": p.get("length"),
            "width_cm": p.get("width"),
            "height_cm": p.get("height"),
            "fulfil_write_date": datetime.fromisoformat(p["write_date"]).astimezone(timezone.utc),
        }

    def _to_shiphero_payload(self, row: Product) -> dict:
        return {
            "sku": row.sku,
            "name": row.variant_name or row.sku,
            "barcode": row.upc,
            "tariff_code": row.hs_code,
            "country_of_manufacture": (row.country_of_origin or None),
            "weight": kg_to_lb(row.weight_kg),
            "height": cm_to_in(row.height_cm),
            "width": cm_to_in(row.width_cm),
            "length": cm_to_in(row.length_cm),
        }









    def run_delta_sync(self):
        db = SessionLocal()
        run = SyncRun(started_at=datetime.now(timezone.utc), status='running',
                      total_polled=0, upserts_to_db=0, pushes_to_shiphero=0, skipped_no_change=0, errors_count=0)
        db.add(run)
        db.commit(); db.refresh(run)
        
        try:
            cursor = self._get_cursor(db)
            since_iso = (cursor.last_write_ts or datetime(1970,1,1,tzinfo=timezone.utc)).isoformat()
            
            logger.info(f"Starting delta sync from {since_iso}")
            products = self.fulfil.delta(since_iso)
            
            for p in products:
                run.total_polled += 1
                try:
                    rec = self._to_db_record(p)
                    
                    # upsert by fulfil_product_id
                    existing = db.execute(select(Product).where(Product.fulfil_product_id==rec['fulfil_product_id'])).scalar_one_or_none()
                    if existing:
                        for k,v in rec.items():
                            setattr(existing, k, v)
                        db.flush()
                        row = existing
                    else:
                        row = Product(**rec)
                        db.add(row)
                        db.flush()
                    run.upserts_to_db += 1

                    payload = self._to_shiphero_payload(row)
                    payload_hash = sha256_json(payload)
                    
                    if payload_hash == row.shiphero_payload_hash:
                        run.skipped_no_change += 1
                        logger.debug(f"SKU {row.sku} unchanged, skipping ShipHero update")
                    else:
                        try:
                            if row.shiphero_product_id:
                                logger.info(f"Updating product {row.sku} in ShipHero")
                                res = self.shiphero.update(payload | {"id": row.shiphero_product_id})
                            else:
                                logger.info(f"Creating product {row.sku} in ShipHero")
                                res = self.shiphero.create(payload)
                            
                            # Handle response
                            product_data = res.get('data', {})
                            create_data = product_data.get('product_create', {})
                            update_data = product_data.get('product_update', {})
                            
                            errors = create_data.get('errors') or update_data.get('errors')
                            node = create_data.get('product') or update_data.get('product')
                            
                            if errors:
                                raise RuntimeError(f"ShipHero API errors: {errors}")
                            
                            if node:
                                row.shiphero_product_id = node.get('id') or row.shiphero_product_id
                            
                            # Update tracking fields
                            row.shiphero_payload_hash = payload_hash
                            row.shiphero_last_push_at = datetime.now(timezone.utc)
                            
                            run.pushes_to_shiphero += 1
                            logger.info(f"Successfully synced {row.sku} to ShipHero")
                            
                        except Exception as e:
                            logger.error(f"Failed to sync {row.sku} to ShipHero: {e}")
                            raise

                    db.commit()
                    # advance cursor per row for crash safety
                    self._advance_cursor(db, row.fulfil_write_date, row.fulfil_product_id)
                    
                except Exception as e:
                    run.errors_count += 1
                    error_details = {
                        'sku': p.get('code'),
                        'fulfil_id': p.get('id'),
                        'stage': 'sync',
                        'error_message': str(e),
                        'payload_snippet': str(p)[:1000]
                    }
                    logger.error(f"Error processing product: {error_details}")
                    
                    db.add(SyncError(
                        sync_run_id=run.id, 
                        sku=p.get('code'), 
                        fulfil_product_id=p.get('id'), 
                        stage='sync', 
                        error_message=str(e), 
                        payload_snippet=str(p)[:1000]
                    ))
                    db.commit()

            run.status = 'success' if run.errors_count == 0 else 'partial'
            logger.info(f"Delta sync completed. Status: {run.status}, Products: {run.total_polled}, Errors: {run.errors_count}")
            
        except Exception as e:
            run.status = 'failed'
            logger.error(f"Delta sync failed: {e}")
            db.add(SyncError(sync_run_id=run.id, stage='run', error_message=str(e)))
        finally:
            run.finished_at = datetime.now(timezone.utc)
            db.commit()
            db.close()
        return run.id
