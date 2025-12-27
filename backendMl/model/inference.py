# [file] model/inference.py
import yaml
import os
import torch
from model.model_arch import WideAndDeep
import logging
import joblib
import pandas as pd
from model.preprocess import load_transaction_features, preprocess_for_inference

config_path = 'config.yaml'
with open(config_path, 'r') as f:
    config = yaml.safe_load(f)

def inference(session, checkpoint_path, logger, max_display=10):
    # 2. 데이터 로딩 및 전처리
    df = load_transaction_features(session)
    wide_features = ['product_id', 'order_id', 'customer_id']
    deep_features = ['order_date', 'product_category', 'quantity', 'avg_price_per_item',
                     'shipping_fee', 'coupon_used', 'gender', 'customer_city',
                     'membership_days', 'gst_rate', 'order_month',
                     'coupon_code', 'discount_value', 'order_amount']

    wide_x, deep_x = preprocess_for_inference(df, wide_features, deep_features)

    logger.info(f"[WIDE INPUT FEATURES] {list(wide_x.columns)}")
    logger.info(f"[DEEP INPUT FEATURES] {list(deep_x.columns)}")
    logger.info(f"[WIDE INPUT SHAPE] {wide_x.shape}")
    logger.info(f"[DEEP INPUT SHAPE] {deep_x.shape}")

    # Tensor 변환
    if isinstance(wide_x, (pd.DataFrame, pd.Series)):
        wide_x = torch.from_numpy(wide_x.to_numpy()).float()
    if isinstance(deep_x, (pd.DataFrame, pd.Series)):
        deep_x = torch.from_numpy(deep_x.to_numpy()).float()

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    wide_x = wide_x.to(device)
    deep_x = deep_x.to(device)

    # 3. Label Encoder 및 클래스 수 결정
    encoder_path = os.path.join(os.path.dirname(checkpoint_path), 'label_encoder.pkl')
    if os.path.exists(encoder_path):
        encoder = joblib.load(encoder_path)
        num_classes = len(encoder.classes_)
        logger.info(f"Label encoder loaded, num_classes={num_classes}")
    else:
        encoder = None
        num_classes = 16
        logger.warning(f"Label encoder 없음, num_classes를 16으로 고정")

    # 4. config에서 wideanddeep_args 불러오기
    wideanddeep_cfg = config.get('wideanddeep_args', {})

    # 5. 모델 초기화 (config.yaml 값 반영)
    model = WideAndDeep(
        wide_input_dim=wide_x.shape[1],
        deep_input_dim=deep_x.shape[1],
        num_classes=num_classes,
        deep_hidden_units=wideanddeep_cfg.get('deep_hidden_units', [128, 64]),
        dropout_p=wideanddeep_cfg.get('dropout_p', 0.0),
        use_softmax=wideanddeep_cfg.get('use_softmax', True),
        batch_norm=wideanddeep_cfg.get('batch_norm', True)
    )

    model.load_state_dict(torch.load(checkpoint_path, map_location=device))
    model.to(device)
    model.eval()

    with torch.no_grad():
        output = model(wide_x, deep_x)
        pred = output.argmax(dim=1).cpu().numpy()

    if encoder is not None:
        pred_label = encoder.inverse_transform(pred)
    else:
        pred_label = pred

    for i in range(min(max_display, len(pred))):
        logger.info(f"[Sample {i}] Prediction={pred[i]} ({pred_label[i]})")

    logger.info(f"Inference 완료, 총 {len(pred)}개 샘플 처리됨.")

    return pred, pred_label, None, None