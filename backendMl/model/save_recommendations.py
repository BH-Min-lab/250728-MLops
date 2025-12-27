# model/save_recommendations.py
import json
from datetime import datetime
from infra.db_models.recommendation import Recommendation
from infra.db_models.enums.model_type import ModelType

def save_recommendations(session, user_ids, recommended_labels, model_type=ModelType.DEEP_LEARNING):
    """
    추천 결과를 DB에 저장하거나 업데이트하는 함수
    
    Args:
        session: DB 세션 (SQLAlchemy 세션)
        user_ids: list of int - 사용자 ID 리스트
        recommended_labels: list of str - 추천 결과 레이블 리스트 (pred_label)
        model_type: ModelType enum - 모델 유형
    
    Returns:
        None
    """
    for user_id, rec_label in zip(user_ids, recommended_labels):
        # 추천 결과를 문자열 형태로 저장 (리스트가 아닌 단일 문자열)
        rec_item_str = rec_label
        
        # 기존 추천 결과가 있으면 조회
        existing_rec = session.query(Recommendation).filter_by(user_id=user_id).first()
        
        if existing_rec:
            # 존재하면 업데이트 (추천 결과 및 기타 정보 갱신)
            existing_rec.recommended_items = rec_item_str
            existing_rec.model_type = model_type
            existing_rec.generated_at = datetime.utcnow()
        else:
            # 없으면 신규 생성
            recommendation = Recommendation(
                user_id=user_id,
                recommended_items=rec_item_str,
                model_type=model_type,
                generated_at=datetime.utcnow()
            )
            session.add(recommendation)
    session.commit()
