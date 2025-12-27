# infra/db_models/coupon.py
from sqlalchemy import Column, Integer, String, DECIMAL, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from infra.db.base import Base

class Coupon(Base):
    __tablename__ = "coupons"

    id = Column(Integer, primary_key=True)
    code = Column(String(50), nullable=False)
    discount_type = Column(String(20))  # 'percent' or 'fixed'
    discount_value = Column(DECIMAL(10, 2))
    valid_from = Column(DateTime)
    valid_to = Column(DateTime)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)

    user_coupons = relationship("UserCoupon", back_populates="coupon")
    orders = relationship("Order", back_populates="coupon")
    category = relationship("Category", back_populates="coupons")


class UserCoupon(Base):
    __tablename__ = "user_coupons"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    coupon_id = Column(Integer, ForeignKey("coupons.id"), nullable=False)
    is_used = Column(Boolean, default=False)
    assigned_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    used_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="user_coupons")
    coupon = relationship("Coupon", back_populates="user_coupons")
