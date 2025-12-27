# [file] curd / write_ml_data.py
# [description] ML용 DB에 주문 관련 특성 데이터를 UPSERT(삽입 또는 업데이트) 하는 기능
import logging
from sqlalchemy import Table, MetaData
from sqlalchemy.dialects.mysql import insert
from infra.db.database import MLEngine

logger = logging.getLogger(__name__)

def insert_transaction_features(session, row_dicts: list[dict]):
    """
    ML DB에 transaction_features 테이블에 row_dicts 목록을 UPSERT 수행.
    - 중복 키 발생 시 기존 데이터 업데이트.
    - 필수 키(order_id, product_id) 검증 후 실행.
    """
    if not row_dicts:
        logger.warning("❗ row_dicts가 비어있음")
        return

    # 1) 검증
    required_keys = {"order_id", "product_id"}
    for row in row_dicts:
        if not required_keys.issubset(row.keys()):
            raise ValueError(f"필수 키 누락된 row: {row}")
    metadata = MetaData()

    # 2) 테이블 메타데이터 동적 로딩
    table = Table('transaction_features', metadata, autoload_with=MLEngine)

    # 3) UPSERT 처리 (중복 시 업데이트, 없으면 INSERT)
    for row in row_dicts:
        stmt = insert(table).values(**row)
        upsert_stmt = stmt.on_duplicate_key_update(**row)
        session.execute(upsert_stmt)
        
    logger.info(f"✅ {len(row_dicts)}건 transaction_features 삽입 또는 업데이트 완료")