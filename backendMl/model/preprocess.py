# [file] model/preprocess.py
import os
import pandas as pd
import logging
from sklearn.preprocessing import LabelEncoder
from infra.db_models.ml_features import TransactionFeatures
import joblib

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s][%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# 절대 경로 기반으로 설정
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENCODER_PATH = os.path.join(BASE_DIR, "model", "model_weight", "label_encoder.pkl")

def load_transaction_features(session):
    rows = session.query(TransactionFeatures).all()

    data = []
    for row in rows:
        data.append({
            "customer_id": f"USER_{row.customer_id}",
            "order_id": f"Transaction_{row.order_id}",
            "order_date": row.order_date,
            "product_id": f"Product_{row.product_id}",
            "product_category": row.product_category,
            "quantity": row.quantity,
            "avg_price_per_item": float(row.avg_price_per_item),
            "shipping_fee": float(row.shipping_fee),
            "coupon_used": "Used",
            "coupon_code": row.coupon_code,
            "customer_city": row.customer_city,
            "gender": row.gender,
            "membership_days": row.membership_days,
            "gst_rate": float(row.gst_rate),
            "order_month": row.order_month,
            "discount_value": float(row.discount_value),
            "order_amount": float(row.order_amount),
            "label": row.label,
            "user_id": f"{row.customer_id}"
        })

    df = pd.DataFrame(data)
    logger.info(f"Loaded {len(df)} rows from DB")
    logger.info(f"Sample data:\n{df.head(3)}")
    return df

def preprocess_for_inference(df, wide_features, deep_features):
    logger.info(f"[현재 작업 디렉토리] {os.getcwd()}")
    exclude_cols = ['user_id', 'label']
    df = df.drop(columns=exclude_cols, errors='ignore')
    df.fillna(0, inplace=True)

    if 'order_date' in df.columns:
        df['order_date'] = pd.to_datetime(df['order_date'])
        df['order_date'] = df['order_date'].dt.month + df['order_date'].dt.day / 31.0

    # product_category: 저장된 인코더 사용 (없으면 새로 인코딩)
    product_category_col = 'product_category'
    if product_category_col in df.columns:
        if os.path.exists(ENCODER_PATH):
            encoder = joblib.load(ENCODER_PATH)
            df[product_category_col] = df[product_category_col].astype(str).apply(
                lambda x: encoder.transform([x])[0] if x in encoder.classes_ else -1
            )
            logger.info(f"[Label encoder loaded] {ENCODER_PATH}, num_classes={len(encoder.classes_)}")
        else:
            logger.warning(f"[라벨 인코더 미존재] {ENCODER_PATH} 인코더를 찾을 수 없습니다. 새로 인코딩합니다.")
            le = LabelEncoder()
            df[product_category_col] = le.fit_transform(df[product_category_col].astype(str))

    # 나머지 범주형 변수들 라벨 인코딩
    for col in wide_features + deep_features:
        if col == product_category_col:
            continue
        if df[col].dtype == 'object':
            le = LabelEncoder()
            df[col] = le.fit_transform(df[col].astype(str))

    wide_df = df[wide_features]
    deep_df = df[deep_features]

    logger.info(f"[WIDE INPUT SHAPE] {wide_df.shape}")
    logger.info(f"[DEEP INPUT SHAPE] {deep_df.shape}")

    return wide_df, deep_df