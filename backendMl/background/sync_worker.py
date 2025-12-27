import logging
import time
from infra.db.database import MainSessionLocal, MLSessionLocal
from service.sync_service import sync_data_to_ml_data

SYNC_INTERVAL = 60 * 60   # To Do. 3분

def sync_worker():
    logging.info("🔄 데이터 동기화 워커 시작")
    while True:
        main_session = None
        ml_session = None
        try:
            main_session = MainSessionLocal()
            ml_session = MLSessionLocal()

            sync_data_to_ml_data(main_session, ml_session)

            main_session.commit()
            ml_session.commit()

            logging.info("✅ 데이터 동기화 완료")

        except Exception as e:
            logging.error(f"❌ 동기화 중 오류 발생: {e}", exc_info=True)
            if main_session:
                try:
                    main_session.rollback()
                except Exception:
                    pass
            if ml_session:
                try:
                    ml_session.rollback()
                except Exception:
                    pass
        finally:
            if main_session:
                main_session.close()
            if ml_session:
                ml_session.close()

        time.sleep(SYNC_INTERVAL)