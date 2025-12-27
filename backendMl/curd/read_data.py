# [file] curd/read_data.py
# [description] 운영 DB 필요한 주문 및 고객 정보를 읽어오는 함수
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from sqlalchemy import func
from sqlalchemy.sql import literal_column
from datetime import datetime, timedelta
import logging

from infra.db_models.user import User, Address
from infra.db_models.order import Order, OrderItem
from infra.db_models.product import Product, Category
from infra.db_models.coupon import Coupon

def get_order_summary(session: Session):
    '''
    운영 DB에서 최근 1년간 주문 내역 및 관련 고객, 상품, 쿠폰 정보 조회
    - 기본 거주지 정보, 회원 가입일로부터 경과일 계산
    - 각 주문의 상품 카테고리, 주문월, 쿠폰 사용 여부 등 상세정보 포함
    - 최대 5건 샘플 데이터 반환 (개발 테스트용)
    '''
    now = datetime.utcnow()
    one_year_ago = now - timedelta(days=365) # To Do. 수집 날짜는 회의를 진행하여 조정

    try:
        default_address_subq = (
            session.query(
                Address.user_id,
                Address.city.label("city"),
                Address.country.label("country"),
            )
            .filter(Address.is_default == True)
            .subquery()
        )

        query = (
            session.query(
                User.id.label("customer_id"),
                Order.id.label("order_id"),
                Order.created_at.label("order_date"),
                OrderItem.product_id,
                Category.name.label("product_category"),
                OrderItem.quantity,
                Order.shipping_fee,
                (Order.coupon_id != None).label("coupon_used"),
                func.coalesce(default_address_subq.c.city, default_address_subq.c.country).label("customer_city"),
                func.timestampdiff(
                    literal_column("DAY"),
                    User.created_at,
                    func.utc_timestamp()   
                ).label("membership_days"),
                Category.gst_rate,
                extract('month', Order.created_at).label("order_month"),
                Coupon.code.label("coupon_code"),
                Coupon.discount_value.label("discount_value"),
                Order.total_price.label("order_amount"),
                User.gender.label("gender"),

                (OrderItem.price / func.nullif(OrderItem.quantity, 0)).label("avg_price_per_item"),
            )
            .join(Order, Order.user_id == User.id)
            .join(OrderItem, OrderItem.order_id == Order.id)
            .join(Product, Product.id == OrderItem.product_id)
            .join(Category, Category.id == Product.category_id)
            .outerjoin(Coupon, Coupon.id == Order.coupon_id)
            .outerjoin(default_address_subq, default_address_subq.c.user_id == User.id)
            .filter(Order.created_at >= one_year_ago, Order.created_at <= now)
        )

        return query.limit(5).all() # To Do. 개발 끝나고는 정리하기

    except Exception as e:
        logging.error(f"get_order_summary 예외: {e}", exc_info=True)