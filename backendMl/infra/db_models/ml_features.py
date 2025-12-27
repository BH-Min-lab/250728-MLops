# infra/db_models/ml_transaction_features.py
from sqlalchemy import Column, Integer, String, DECIMAL, DateTime, Boolean
from infra.db.base import Base

class TransactionFeatures(Base):
    __tablename__ = "transaction_features"
    __table_args__ = {"schema": "ml_data"}  # 스키마 지정

    customer_id = Column(Integer)
    order_id = Column(Integer, primary_key=True)
    order_date = Column(DateTime)
    product_id = Column(Integer, primary_key=True)
    product_category = Column(String(100))
    quantity = Column(Integer)
    avg_price_per_item = Column(DECIMAL(10, 2))
    shipping_fee = Column(DECIMAL(10, 2))
    coupon_used = Column(Boolean)
    customer_city = Column(String(100))
    gender = Column(String(10))   
    membership_days = Column(Integer)
    gst_rate = Column(DECIMAL(5, 2))
    order_month = Column(Integer)
    coupon_code = Column(String(50))
    discount_value = Column(DECIMAL(10, 2))
    order_amount = Column(DECIMAL(10, 2))
    label = Column(Integer, nullable=True)