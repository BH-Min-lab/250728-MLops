# [file] service / sync_service.py
# [description] 운영 DB에서 원시 데이터를 읽어와 ML DB에 삽입하는 동기화 로직 구현
import logging
from curd.read_data import get_order_summary
from curd.write_ml_data import insert_transaction_features
from curd.write_main_data import delete_processed_orders 

def sync_data_to_ml_data(main_session, ml_session):
    """
    1) 운영 DB에서 최근 주문 데이터 조회
    2) SQLAlchemy 결과를 딕셔너리 리스트로 변환
    3) ML DB에 삽입 (UPSERT)
    4) 처리 완료된 주문 ID를 운영 DB에서 삭제 (현재 주석 혹은 비활성화 상태)
    """
    # 1) 운영 DB에서 최근 주문 데이터 조회
    raw_data = get_order_summary(main_session)
    if not raw_data:
        logging.info("🚫 처리할 주문 없음")
        return

    # 2) SQLAlchemy 결과를 딕셔너리 리스트로 변환
    rows = transform_to_row_dict(raw_data)

    # 3) ML DB에 삽입 (UPSERT)
    insert_transaction_features(ml_session, rows)

    # 4) 처리 완료된 주문 ID를 운영 DB에서 삭제 (현재 주석 혹은 비활성화 상태)
    order_ids = [r["order_id"] for r in rows]
    delete_processed_orders(main_session, order_ids)

    logging.info(f"📦 처리 완료: {len(rows)}건")

def transform_to_row_dict(order_data):
    """
    SQLAlchemy 쿼리 결과 객체 리스트를 ML DB 삽입용 dict 리스트로 변환
    - 타입 캐스팅 및 기본값 처리 포함
    """
    return [
        {
            "customer_id": r.customer_id,
            "order_id": r.order_id,
            "order_date": r.order_date,
            "product_id": r.product_id,
            "product_category": r.product_category,
            "quantity": r.quantity,
            "avg_price_per_item": float(r.avg_price_per_item),
            "shipping_fee": float(r.shipping_fee),
            "coupon_used": bool(r.coupon_used),
            "customer_city": r.customer_city,
            "gender": r.gender,  
            "membership_days": int(r.membership_days),
            "gst_rate": float(r.gst_rate),
            "order_month": int(r.order_month),
            "coupon_code": r.coupon_code,
            "discount_value": float(r.discount_value or 0),
            "order_amount": float(r.order_amount),
            "label": None
        }
        for r in order_data
    ]
