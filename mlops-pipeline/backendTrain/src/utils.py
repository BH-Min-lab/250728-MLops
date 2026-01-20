# utils.py

import os
import random
import numpy as np
import torch
import pandas as pd
from minio import Minio


CATEGORY_MAP = {
    'Fun': 'Lifestyle',
    'More Bags': 'Bags',
    'Backpacks': 'Bags',
    'Google': 'Nest'
}

MONTH_MAP = {
    1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr',
    5: 'May', 6: 'Jun', 7: 'Jul', 8: 'Aug',
    9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'
}


def get_data_path(symbol, data_dir, minio_endpoint="127.0.0.1:9000",
                  minio_access_key="admin", minio_secret_key="admin",
                  raw_data_bucket="raw-data"):
    """
    Get the local path for a CSV file, downloading from MinIO raw_data bucket if needed.
    """
    mapping = {
        'Customer': 'Customer_info.csv',
        'Discount': 'Discount_info.csv',
        'Onlinesales': 'Onlinesales_info.csv',
        'Tax': 'Tax_info.csv',
        'Marketing': 'Marketing_info.csv'
    }
    if symbol not in mapping:
        raise ValueError(
            f"Symbol '{symbol}' is not recognized. Allowed values: {list(mapping.keys())}")

    client = Minio(
        minio_endpoint,
        access_key=minio_access_key,
        secret_key=minio_secret_key,
        secure=False
    )

    local_path = os.path.join(data_dir, mapping[symbol])
    try:
        client.fget_object(raw_data_bucket, mapping[symbol], local_path)
        print(
            f"Downloaded {mapping[symbol]} from MinIO: {raw_data_bucket}/{mapping[symbol]}")
    except Exception as e:
        print(f"Failed to download {mapping[symbol]} from MinIO: {e}")
        if not os.path.exists(local_path):
            raise FileNotFoundError(
                f"{mapping[symbol]} not found locally or in MinIO")

    return local_path


def fix_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    torch.manual_seed(seed)
    torch.use_deterministic_algorithms(False)


def mapping_columns(columns):
    mapping_dict = {
        '고객ID': 'customer_id',
        '거래ID': 'order_id',
        '거래날짜': 'order_date',
        '제품ID': 'product_id',
        '제품카테고리': 'product_category',
        '수량': 'quantity',
        '평균금액': 'avg_price_per_item',
        '배송료': 'shipping_fee',
        '쿠폰상태': 'coupon_used',
        '성별': 'gender',
        '고객지역': 'customer_city',
        '가입기간': 'membership_days',
        'GST': 'gst_rate',
        '월': 'order_month',
        '쿠폰코드': 'coupon_code',
        '할인율': 'discount_value',
        '거래금액': 'order_amount'
    }
    return [mapping_dict.get(col, col) for col in columns]


def split_wide_deep_by_type(df: pd.DataFrame, wide_cat_cols=None):
    """
    범주형 컬럼은 wide, 수치형 컬럼은 deep으로 자동 분리

    Parameters:
        df: pd.DataFrame (입력 피처 전체 포함)
        wide_cat_cols: 명시적으로 wide로 강제할 컬럼 목록 (optional)

    Returns:
        wide_x: np.ndarray
        deep_x: np.ndarray
    """
    # 명시적 범주형이 주어지면 사용, 아니면 자동 탐지
    if wide_cat_cols is None:
        inferred_cats = df.select_dtypes(
            include=['object', 'category']).columns.tolist()
        inferred_cats += [col for col in df.columns if 'id' in col or col in [
            '성별', '월', '쿠폰코드', '고객지역', '쿠폰상태']]
        wide_cat_cols = list(set(inferred_cats) & set(df.columns))

    # 나머지는 deep
    deep_cols = [col for col in df.columns if col not in wide_cat_cols]

    wide_x = df[wide_cat_cols].to_numpy().astype(float)
    deep_x = df[deep_cols].to_numpy().astype(float)

    return wide_x, deep_x


class MetricTracker:
    def __init__(self, *keys):
        self._data = pd.DataFrame(
            index=keys, columns=['total', 'counts', 'average'])
        self.reset()

    def reset(self):
        for col in self._data.columns:
            self._data[col].values[:] = 0

    def update(self, key, value, n=1):
        # pandas 3.0 경고 해결: loc 사용
        self._data.loc[key, 'total'] += value * n
        self._data.loc[key, 'counts'] += n
        self._data.loc[key, 'average'] = (
            self._data.loc[key, 'total'] / self._data.loc[key, 'counts']
        )

    def avg(self, key):
        return self._data.loc[key, 'average']

    def result(self):
        return dict(self._data['average'])
