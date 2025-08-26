from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from sqlalchemy import Text, TIMESTAMP, Boolean, Numeric, Integer
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
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Fulfil Product ID
    fulfil_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    
    # ShipHero Product ID
    shiphero_id: Mapped[str] = mapped_column(Text, nullable=True)

    # Fulfil product identifiers
    code: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
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
        return {
            "name": self.name,
            "sku": self.code,
            "barcode": self.upc or self.code,
            "country_of_manufacture": self.country_of_origin or "US",
            "dimensions": {
                "weight": str(self.weight_gm or 0),
                "height": str(self.height_cm or 0),
                "width": str(self.width_cm or 0),
                "length": str(self.length_cm or 0)
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

class ProductSyncLog(Base):
    __tablename__ = "product_sync_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    product_code: Mapped[str] = mapped_column(Text, nullable=False)
    product_name: Mapped[str] = mapped_column(Text, nullable=False)
    action: Mapped[str] = mapped_column(Text, nullable=False)  # 'created' or 'updated'
    changed_fields: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON string of changed fields
    synced_at: Mapped[str] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
