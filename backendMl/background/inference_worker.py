# [file] inference_worker.py
import logging
import time
from model.inference import inference
from model.save_recommendations import save_recommendations
from infra.db.database import MLSessionLocal, MainSessionLocal
from infra.db_models.enums.model_type import ModelType

INFERENCE_INTERVAL = 60 * 60 * 24  # 하루에 한 번

def inference_worker():
    logging.info("🧠 추론 워커 시작")
    while True:
        ml_session = None
        main_session = None
        try:
            ml_session = MLSessionLocal()
            main_session = MainSessionLocal()

            checkpoint_path = "model/model_weight/model_v1.pt"

            # 1. 추론 수행 (ML DB 세션)
            pred, pred_label, _, _ = inference(
                session=ml_session,
                checkpoint_path=checkpoint_path,
                logger=logging.getLogger(),
                max_display=5
            )

            # 2. 사용자 ID 불러오기 (ML DB 세션)
            from model.preprocess import load_transaction_features
            df = load_transaction_features(ml_session)
            user_ids = df['user_id'].tolist()

            # 3. 추천 결과 저장 (메인 DB 세션 사용)
            save_recommendations(
                session=main_session,
                user_ids=user_ids,
                recommended_labels=pred_label,
                model_type=ModelType.DEEP_LEARNING
            )

            logging.info("✅ 추론 및 추천 저장 작업 완료")

        except Exception as e:
            logging.error(f"❌ 추론 중 오류 발생: {e}", exc_info=True)

        finally:
            if ml_session:
                ml_session.close()
            if main_session:
                main_session.close()

        time.sleep(INFERENCE_INTERVAL)
