import os
import numpy as np
import pandas as pd
import joblib
from minio import Minio
from utils import get_data_path, mapping_columns, split_wide_deep_by_type, CATEGORY_MAP, MONTH_MAP

import torch
from torch.utils.data import Dataset
from sklearn.preprocessing import LabelEncoder
from pathlib import Path

print("Current Working Directory:", os.getcwd())
SYMBOLS = ['Customer', 'Discount', 'Marketing',
           'Onlinesales', 'Tax']  # !!! 수정 금지 !!!


class InfoDataset(Dataset):
    def __init__(self, is_training=True, in_columns=None, out_columns=None, data_dir='/opt/airflow/data',
                 new_onlinesales_path=None, minio_endpoint="127.0.0.1:9000",
                 minio_access_key="admin", minio_secret_key="admin",
                 raw_data_bucket="raw-data", new_sales_bucket="new-sales", **kwargs):
        if in_columns is None:
            in_columns = ['고객ID', '거래ID', '거래날짜', '제품ID', '제품카테고리', '수량', '평균금액', '배송료', '쿠폰상태',
                          '성별', '고객지역', '가입기간', 'GST', '월', '쿠폰코드', '할인율', '거래금액']
        if out_columns is None:
            out_columns = ['제품카테고리']

        print("[DEBUG] MinIO endpoint:", minio_endpoint)

        self.minio_client = Minio(
            minio_endpoint,
            access_key=minio_access_key,
            secret_key=minio_secret_key,
            secure=False
        )
        self.raw_data_bucket = raw_data_bucket
        self.new_sales_bucket = new_sales_bucket

        (wide_x, deep_x), self.y = make_features(
            in_columns, out_columns, is_training, data_dir, new_onlinesales_path,
            minio_endpoint, minio_access_key, minio_secret_key, raw_data_bucket, new_sales_bucket
        )
        self.wide_x = torch.from_numpy(wide_x).float()
        self.deep_x = torch.from_numpy(deep_x).float()
        self.y = torch.from_numpy(self.y).float()

    def __len__(self):
        return len(self.y)

    def __getitem__(self, idx):
        return (self.wide_x[idx], self.deep_x[idx]), self.y[idx]


def merge_data(symbols, data_dir, new_onlinesales_path=None,
               minio_endpoint="127.0.0.1:9000", minio_access_key="admin",
               minio_secret_key="admin", raw_data_bucket="raw-data", new_sales_bucket="new-sales"):
    print("merging raw csv files...")

    # 기본 5종 로드
    dfs = {symbol: pd.read_csv(get_data_path(
        symbol, data_dir, minio_endpoint, minio_access_key, minio_secret_key, raw_data_bucket))
        for symbol in symbols}

    for name, df in dfs.items():
        print(f"[DEBUG] {name} rows: {len(df)}")

    # 새 거래 CSV가 지정된 경우에만 시도
    if new_onlinesales_path:
        client = Minio(minio_endpoint, access_key=minio_access_key,
                       secret_key=minio_secret_key, secure=False)
        fetched = False
        try:
            # 오브젝트 존재 확인 후 다운로드
            client.stat_object(new_sales_bucket, "Onlinesales_new.csv")
            client.fget_object(
                new_sales_bucket, "Onlinesales_new.csv", new_onlinesales_path)
            print(
                f"Downloaded Onlinesales_new.csv from MinIO: {new_sales_bucket}/Onlinesales_new.csv")
            fetched = True
        except Exception as e:
            print(f"[INFO] MinIO 에서 Onlinesales_new.csv 확인/다운로드 실패: {e}")

        # 로컬에 있으면 사용 (MinIO 실패시 대체)
        if fetched or os.path.exists(new_onlinesales_path):
            new_df = pd.read_csv(new_onlinesales_path)
            # 기존 Onlinesales 에 "추가"
            dfs['Onlinesales'] = pd.concat(
                [dfs['Onlinesales'], new_df], ignore_index=True)
            print(
                f"[DEBUG] Onlinesales rows after concat: {len(dfs['Onlinesales'])}")
        else:
            print("[INFO] Onlinesales_new.csv 가 MinIO/로컬에 없음. 새 거래 병합 생략.")

    # 병합 순서: Onlinesales + Customer → Tax → Discount
    merged = pd.merge(dfs['Onlinesales'], dfs['Customer'], on='고객ID')
    merged = pd.merge(merged, dfs['Tax'], on='제품카테고리')

    # 제품카테고리 매핑
    merged['제품카테고리'] = merged['제품카테고리'].map(
        CATEGORY_MAP).fillna(merged['제품카테고리'])

    # Discount에서 'Notebooks' 제외
    discount_df = dfs['Discount'][dfs['Discount']
                                  ['제품카테고리'] != 'Notebooks'].copy()

    # 월 파생 후 문자열로 매핑
    merged['월'] = pd.to_datetime(merged['거래날짜']).dt.month.map(MONTH_MAP)

    # Discount 병합
    merged = pd.merge(merged, discount_df, on=['제품카테고리', '월'])

    # 거래날짜 정수화
    merged['거래날짜'] = pd.to_datetime(merged['거래날짜'], errors='coerce')
    merged['거래날짜'] = merged['거래날짜'].dt.strftime('%Y%m%d').astype(float)

    # 거래금액 공식 적용
    merged['거래금액'] = merged['평균금액'] * merged['수량'] * \
        (1 + merged['GST']) + merged['배송료']

    print("🔍 최종 병합된 컬럼 목록:", merged.columns.tolist())
    return merged


def make_features(in_columns, out_columns, is_training, data_dir='/opt/airflow/data', new_onlinesales_path=None,
                  minio_endpoint="127.0.0.1:9000", minio_access_key="admin",
                  minio_secret_key="admin", raw_data_bucket="raw-data", new_sales_bucket="new-sales"):

    save_fname = 'merged_data.pkl'

    merged_path = Path(data_dir) / save_fname
    label_path = Path(data_dir) / "label_encoder.pkl"

    client = Minio(minio_endpoint, access_key=minio_access_key,
                   secret_key=minio_secret_key, secure=False)

    # Download merged_data.pkl from MinIO if exists
    if not new_onlinesales_path and os.path.exists(merged_path):
        print(f'loading from {merged_path}')
        df = pd.read_pickle(merged_path)
    else:
        print('merging raw csv files...')
        df = merge_data(SYMBOLS, data_dir, new_onlinesales_path,
                        minio_endpoint, minio_access_key, minio_secret_key, raw_data_bucket, new_sales_bucket)
        df.to_pickle(merged_path)
        print(f'saved to {merged_path}')
        # Upload to MinIO raw_data bucket
        try:
            client.fput_object(raw_data_bucket, save_fname, merged_path)
            print(
                f"Uploaded {save_fname} to MinIO: {raw_data_bucket}/{save_fname}")
        except Exception as e:
            print(f"Failed to upload {save_fname} to MinIO: {e}")

    df.dropna(subset=out_columns, inplace=True)
    df.fillna(0, inplace=True)

    # 문자열형 컬럼 인코딩
    label_cols = ['성별', '고객지역', '쿠폰코드', '월', '고객ID', '거래ID', '제품ID', '쿠폰상태']
    for col in label_cols:
        if col in df.columns:
            df[col] = LabelEncoder().fit_transform(df[col].astype(str))

    # 타겟 인코딩
    if is_training:
        encoder = LabelEncoder()
        df[out_columns[0]] = encoder.fit_transform(df[out_columns[0]])
        joblib.dump(encoder, label_path)
        print(f"🔒 LabelEncoder 저장됨: {label_path}")
        # Upload to MinIO raw_data bucket
        try:
            client.fput_object(
                raw_data_bucket, 'label_encoder.pkl', label_path)
            print(
                f"Uploaded label_encoder.pkl to MinIO: {raw_data_bucket}/label_encoder.pkl")
        except Exception as e:
            print(f"Failed to upload label_encoder.pkl to MinIO: {e}")
    else:
        try:
            client.fget_object(
                raw_data_bucket, 'label_encoder.pkl', label_path)
            print(
                f"Downloaded label_encoder.pkl from MinIO: {raw_data_bucket}/label_encoder.pkl")
        except Exception as e:
            print(f"Failed to download label_encoder.pkl from MinIO: {e}")
        encoder = joblib.load(label_path)
        try:
            df[out_columns[0]] = encoder.transform(df[out_columns[0]])
        except ValueError as e:
            print(f"Error in LabelEncoder: {e}. Re-fitting encoder.")
            encoder = LabelEncoder()
            df[out_columns[0]] = encoder.fit_transform(df[out_columns[0]])
            joblib.dump(encoder, label_path)
            try:
                client.fput_object(
                    raw_data_bucket, 'label_encoder.pkl', label_path)
                print(
                    f"Uploaded updated label_encoder.pkl to MinIO: {raw_data_bucket}/label_encoder.pkl")
            except Exception as e:
                print(f"Failed to upload label_encoder.pkl to MinIO: {e}")
        print(f"📦 LabelEncoder 로드됨: {label_path}")

    df = df[in_columns + out_columns]
    df = df.loc[:, ~df.columns.duplicated()]

    df.columns = mapping_columns(df.columns.tolist())
    in_columns = mapping_columns(in_columns)
    out_columns = mapping_columns(out_columns)

    x_df = df[in_columns]
    y = df[out_columns].to_numpy().astype(float).squeeze()

    wide_x, deep_x = split_wide_deep_by_type(x_df)

    return ((wide_x[:-100], deep_x[:-100]), y[:-100]) if is_training else ((wide_x[-100:], deep_x[-100:]), y[-100:])


if __name__ == "__main__":
    dataset = InfoDataset(
        is_training=True,
        new_onlinesales_path="../data/Onlinesales_new.csv",
        minio_endpoint="127.0.0.1:9000",
        minio_access_key="admin",
        minio_secret_key="admin",
        raw_data_bucket="raw-data",
        new_sales_bucket="new-sales"
    )
    print(f"dataset length: {len(dataset)}")
    print(
        f"wide_x shape: {dataset.wide_x.shape}, deep_x shape: {dataset.deep_x.shape}, y shape: {dataset.y.shape}")
    print("first sample wide_x:", dataset[0][0][0])
    print("first sample deep_x:", dataset[0][0][1])
    print("first sample y:", dataset[0][1])

    # ✅ 클래스 수 확인
    import numpy as np
    unique_classes, counts = np.unique(dataset.y.numpy(), return_counts=True)
    print("\n📊 클래스 개수:", len(unique_classes))
    print("🧩 클래스 목록:", unique_classes.tolist())
    print("🔢 클래스별 샘플 수:")
    for c, n in zip(unique_classes, counts):
        print(f" - 클래스 {int(c)}: {n}개")

    # ✅ 입력 피처 구성 확인
    in_columns = [
        '고객ID', '거래ID', '거래날짜', '제품ID', '제품카테고리', '수량', '평균금액', '배송료', '쿠폰상태',
        '성별', '고객지역', '가입기간', 'GST', '월', '쿠폰코드', '할인율', '거래금액']
    in_columns = mapping_columns(in_columns)
    print("\n🧾 입력 피처 목록:")
    for idx, col in enumerate(in_columns):
        print(f"[{idx}] {col}")
