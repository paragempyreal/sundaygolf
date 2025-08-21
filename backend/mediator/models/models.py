from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from sqlalchemy import BigInteger, Text, Numeric, TIMESTAMP, CheckConstraint, ForeignKey, Boolean, Integer
from sqlalchemy.sql import func

Base = declarative_base()

class Product(Base):
    __tablename__ = "product"
    id: Mapped[int] = mapped_column(primary_key=True)
    fulfil_product_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    sku: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    variant_name: Mapped[str | None] = mapped_column(Text)
    upc: Mapped[str | None] = mapped_column(Text)
    hs_code: Mapped[str | None] = mapped_column(Text)
    country_of_origin: Mapped[str | None] = mapped_column(Text)
    weight_kg: Mapped[float | None] = mapped_column(Numeric(12,4))
    length_cm: Mapped[float | None] = mapped_column(Numeric(12,4))
    width_cm:  Mapped[float | None] = mapped_column(Numeric(12,4))
    height_cm: Mapped[float | None] = mapped_column(Numeric(12,4))
    fulfil_write_date: Mapped[str] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    shiphero_product_id: Mapped[str | None] = mapped_column(Text)
    shiphero_last_push_at: Mapped[str | None] = mapped_column(TIMESTAMP(timezone=True))
    shiphero_payload_hash: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[str] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

class SyncRun(Base):
    __tablename__ = "sync_run"
    id: Mapped[int] = mapped_column(primary_key=True)
    started_at: Mapped[str] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    finished_at: Mapped[str | None] = mapped_column(TIMESTAMP(timezone=True))
    status: Mapped[str] = mapped_column(Text, nullable=False)
    total_polled: Mapped[int | None]
    upserts_to_db: Mapped[int | None]
    pushes_to_shiphero: Mapped[int | None]
    skipped_no_change: Mapped[int | None]
    errors_count: Mapped[int | None]
    __table_args__ = (CheckConstraint("status in ('running','success','partial','failed')"),)

class SyncError(Base):
    __tablename__ = "sync_error"
    id: Mapped[int] = mapped_column(primary_key=True)
    sync_run_id: Mapped[int | None] = mapped_column(ForeignKey("sync_run.id"))
    sku: Mapped[str | None] = mapped_column(Text)
    fulfil_product_id: Mapped[int | None] = mapped_column(BigInteger)
    stage: Mapped[str | None] = mapped_column(Text)
    error_message: Mapped[str | None] = mapped_column(Text)
    payload_snippet: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())

class ShipHeroToken(Base):
    __tablename__ = "shiphero_token"
    id: Mapped[int] = mapped_column(primary_key=True)
    access_token: Mapped[str] = mapped_column(Text, nullable=False)
    refresh_token: Mapped[str] = mapped_column(Text, nullable=False)
    expires_at: Mapped[str] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    created_at: Mapped[str] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())

class FulfilCursor(Base):
    __tablename__ = "fulfil_cursor"
    id: Mapped[int] = mapped_column(primary_key=True)
    last_write_ts: Mapped[str | None] = mapped_column(TIMESTAMP(timezone=True))
    last_id: Mapped[int | None] = mapped_column(BigInteger)

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

class EmailConfiguration(Base):
    __tablename__ = "email_configuration"
    id: Mapped[int] = mapped_column(primary_key=True)
    smtp_host: Mapped[str] = mapped_column(Text, nullable=False)
    smtp_port: Mapped[int] = mapped_column(Integer, nullable=False)
    smtp_username: Mapped[str] = mapped_column(Text, nullable=False)
    smtp_password: Mapped[str] = mapped_column(Text, nullable=False)
    smtp_use_tls: Mapped[bool] = mapped_column(Boolean, default=True)
    smtp_use_ssl: Mapped[bool] = mapped_column(Boolean, default=False)
    from_email: Mapped[str] = mapped_column(Text, nullable=False)
    from_name: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[str] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[str] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
