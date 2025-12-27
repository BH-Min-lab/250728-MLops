# infra/db_models/user.py
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from infra.db.base import Base
from infra.db_models.enums.gender import Gender
from infra.db_models.enums.user_role import UserRole  # 고객/관리자 구분 enum

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)
    nickname = Column(String(100), unique=True, nullable=False)
    age = Column(Integer)
    gender = Column(SqlEnum(
        Gender,
        name="gender_enum",
        native_enum=False,
        values_callable=lambda enum: [e.value for e in enum]
    ), nullable=True)  
    role = Column(SqlEnum(UserRole), default=UserRole.CUSTOMER, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # relationships
    profile = relationship("UserProfile", back_populates="user", uselist=False)
    products = relationship("Product", back_populates="seller")
    orders = relationship("Order", back_populates="buyer")
    cart_items = relationship("CartItem", back_populates="user")
    addresses = relationship("Address", back_populates="user")
    reviews = relationship("ProductReview", back_populates="user")
    user_coupons = relationship("UserCoupon", back_populates="user")
    recommendations = relationship("Recommendation", back_populates="user")

class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    bio = Column(Text)
    avatar_url = Column(String(255))

    user = relationship("User", back_populates="profile")


class Address(Base):
    __tablename__ = "addresses"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    country = Column(String(100), nullable=False)
    state = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    street_address = Column(String(255), nullable=True)
    postal_code = Column(String(20), nullable=True)
    is_default = Column(Boolean, default=False)

    user = relationship("User", back_populates="addresses")
