from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Retailer(Base):
    __tablename__ = "retailers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True)


class ProductCanonical(Base):
    __tablename__ = "product_canonical"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    canonical_name: Mapped[str] = mapped_column(String(255), index=True)
    normalized_title: Mapped[str] = mapped_column(String(255), index=True)
    brand: Mapped[str | None] = mapped_column(String(100), nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    size_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    size_unit: Mapped[str | None] = mapped_column(String(20), nullable=True)
    own_brand: Mapped[bool] = mapped_column(Boolean, default=False)


class ProductRaw(Base):
    __tablename__ = "product_raw"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    retailer_id: Mapped[int] = mapped_column(ForeignKey("retailers.id"))
    provider_sku: Mapped[str] = mapped_column(String(100), index=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    normalized_title: Mapped[str] = mapped_column(String(255), index=True)
    brand: Mapped[str | None] = mapped_column(String(100), nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    size_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    size_unit: Mapped[str | None] = mapped_column(String(20), nullable=True)
    own_brand: Mapped[bool] = mapped_column(Boolean, default=False)
    canonical_id: Mapped[int | None] = mapped_column(ForeignKey("product_canonical.id"), nullable=True)

    retailer = relationship("Retailer")


class ProductPriceSnapshot(Base):
    __tablename__ = "product_price_snapshot"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_raw_id: Mapped[int] = mapped_column(ForeignKey("product_raw.id"))
    price: Mapped[float] = mapped_column(Float)
    unit_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    captured_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ProductMatch(Base):
    __tablename__ = "product_match"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    query_text: Mapped[str] = mapped_column(String(255))
    raw_product_id: Mapped[int] = mapped_column(ForeignKey("product_raw.id"))
    confidence_label: Mapped[str] = mapped_column(String(20))
    confidence_score: Mapped[float] = mapped_column(Float)
    uncertainty_note: Mapped[str | None] = mapped_column(Text, nullable=True)


class Basket(Base):
    __tablename__ = "baskets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(255), default="My Basket")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class BasketItem(Base):
    __tablename__ = "basket_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    basket_id: Mapped[int] = mapped_column(ForeignKey("baskets.id"))
    query_text: Mapped[str] = mapped_column(String(255))
    quantity: Mapped[int] = mapped_column(Integer, default=1)


class SavedList(Base):
    __tablename__ = "saved_lists"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(255))
    items_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
