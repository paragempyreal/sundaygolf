from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from sqlalchemy import Text, TIMESTAMP, Boolean, Numeric, Integer, UniqueConstraint, Index
from sqlalchemy.sql import func

Base = declarative_base()

class Configuration(Base):
    __tablename__ = "configuration"
    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    is_sensitive: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[str] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[str] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    email: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[str] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[str] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

class Product(Base):
    __tablename__ = "products"
    __table_args__ = (
        UniqueConstraint('mode', 'fulfil_id', name='uq_products_mode_fulfil_id'),
        UniqueConstraint('mode', 'code', name='uq_products_mode_code'),
        Index('ix_products_mode', 'mode'),
    )
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # Environment mode: 'live' or 'test'
    mode: Mapped[str] = mapped_column(Text, nullable=False, default='live')
    
    # Fulfil Product ID (unique per mode)
    fulfil_id: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # ShipHero Product ID
    shiphero_id: Mapped[str] = mapped_column(Text, nullable=True)

    # Fulfil product identifiers (unique per mode)
    code: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    template_name: Mapped[str] = mapped_column(Text, nullable=True)
    category_name: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Product attributes
    variant_name: Mapped[str] = mapped_column(Text, nullable=True)
    upc: Mapped[str] = mapped_column(Text, nullable=True)
    asin: Mapped[str] = mapped_column(Text, nullable=True)
    buyer_sku: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Dimensions and weight
    weight_gm: Mapped[float] = mapped_column(Numeric, nullable=True)
    weight_oz: Mapped[float] = mapped_column(Numeric, nullable=True)
    length_cm: Mapped[float] = mapped_column(Numeric, nullable=True)
    width_cm: Mapped[float] = mapped_column(Numeric, nullable=True)
    height_cm: Mapped[float] = mapped_column(Numeric, nullable=True)
    length_in: Mapped[float] = mapped_column(Numeric, nullable=True)
    width_in: Mapped[float] = mapped_column(Numeric, nullable=True)
    height_in: Mapped[float] = mapped_column(Numeric, nullable=True)
    
    # Units of measure
    dimension_unit: Mapped[str] = mapped_column(Text, nullable=True)
    weight_uom: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Customs information
    country_of_origin: Mapped[str] = mapped_column(Text, nullable=True)
    hs_code: Mapped[str] = mapped_column(Text, nullable=True)
    customs_description: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Other product information
    quantity_per_case: Mapped[int] = mapped_column(Integer, nullable=True)
    unit_of_measure: Mapped[str] = mapped_column(Text, nullable=True)
    image_url: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Timestamps
    last_synced_at: Mapped[str] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    created_at: Mapped[str] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[str] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def to_fulfil_dict(self):
        """Convert product to Fulfil API format"""
        return {
            "id": self.fulfil_id,
            "code": self.code,
            "upc": self.upc,
            "name": self.name,
            "template_name": self.template_name,
            "category_name": self.category_name,
            "customs_information": {
                "hs_code": self.hs_code,
                "country_of_origin": self.country_of_origin,
                "customs_description": self.customs_description
            },
            "image_url": self.image_url,
            "quantity_per_case": self.quantity_per_case,
            "weight": {
                "weight_gm": float(self.weight_gm) if self.weight_gm else None,
                "weight_oz": float(self.weight_oz) if self.weight_oz else None
            },
            "dimensions": {
                "length_cm": float(self.length_cm) if self.length_cm else None,
                "width_cm": float(self.width_cm) if self.width_cm else None,
                "height_cm": float(self.height_cm) if self.height_cm else None,
                "length_in": float(self.length_in) if self.length_in else None,
                "width_in": float(self.width_in) if self.width_in else None,
                "height_in": float(self.height_in) if self.height_in else None
            }
        }
    
    def to_shiphero_dict(self):
        """Convert product to ShipHero API format"""
        # Convert dimensions from cm to inches if cm values exist, otherwise use inch values
        def get_dimension_in_inches(cm_value, inch_value):
            if cm_value is not None:
                # Convert Decimal to float first, then convert cm to inches (1 cm = 0.393701 inches)
                cm_float = float(cm_value) if hasattr(cm_value, '__float__') else float(cm_value or 0)
                return round(cm_float * 0.393701, 4)
            elif inch_value is not None:
                # Convert Decimal to float
                return float(inch_value) if hasattr(inch_value, '__float__') else float(inch_value or 0)
            return 0.0
        
        # Convert weight from grams to pounds if gm values exist, otherwise use oz values
        def get_weight_in_pounds(gm_value, oz_value):
            if gm_value is not None:
                # Convert Decimal to float first, then convert grams to pounds (1 gram = 0.00220462 pounds)
                gm_float = float(gm_value) if hasattr(gm_value, '__float__') else float(gm_value or 0)
                return round(gm_float * 0.00220462, 4)
            elif oz_value is not None:
                # Convert Decimal to float first, then convert ounces to pounds (1 ounce = 0.0625 pounds)
                oz_float = float(oz_value) if hasattr(oz_value, '__float__') else float(oz_value or 0)
                return round(oz_float * 0.0625, 4)
            return 0.0
        
        # Get dimensions in inches
        length_inches = get_dimension_in_inches(self.length_cm, self.length_in)
        width_inches = get_dimension_in_inches(self.width_cm, self.width_in)
        height_inches = get_dimension_in_inches(self.height_cm, self.height_in)
        
        # Get weight in pounds
        weight_pounds = get_weight_in_pounds(self.weight_gm, self.weight_oz)
        
        # Ensure we have valid numeric values
        if not isinstance(length_inches, (int, float)) or length_inches < 0:
            length_inches = 0.0
        if not isinstance(width_inches, (int, float)) or width_inches < 0:
            width_inches = 0.0
        if not isinstance(height_inches, (int, float)) or height_inches < 0:
            height_inches = 0.0
        if not isinstance(weight_pounds, (int, float)) or weight_pounds < 0:
            weight_pounds = 0.0
        
        # Try sending weight as a separate field first, then in dimensions
        base_data = {
            "name": self.name,
            "sku": self.code,
            "barcode": self.upc or self.code,
            "country_of_manufacture": self.country_of_origin or "US",
            "dimensions": {
                "height": height_inches,      # Send as numeric value
                "width": width_inches,        # Send as numeric value
                "length": length_inches       # Send as numeric value
                # Removed weight from dimensions - ShipHero might expect it elsewhere
            },
            "tariff_code": self.hs_code,
            "customs_description": self.customs_description or self.name,
            "kit": False,
            "kit_build": False,
            "no_air": False,
            "final_sale": False,
            "customs_value": "0.00",
            "not_owned": False,
            "dropship": False
        }
        
        # Add weight as a separate field if it's not zero
        if weight_pounds > 0:
            base_data["weight"] = weight_pounds
        
        return base_data

class ProductSyncLog(Base):
    __tablename__ = "product_sync_logs"
    __table_args__ = (
        Index('ix_product_sync_logs_mode', 'mode'),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # Environment mode: 'live' or 'test'
    mode: Mapped[str] = mapped_column(Text, nullable=False, default='live')
    product_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    product_code: Mapped[str] = mapped_column(Text, nullable=False)
    product_name: Mapped[str] = mapped_column(Text, nullable=False)
    action: Mapped[str] = mapped_column(Text, nullable=False)  # 'created' or 'updated'
    changed_fields: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON string of changed fields
    synced_at: Mapped[str] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
