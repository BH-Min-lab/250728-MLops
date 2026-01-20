import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from minio import Minio
from utils import get_data_path, mapping_columns, CATEGORY_MAP, MONTH_MAP
import re
import pandas as pd
import numpy as np


def generate_new_onlinesales(data_dir="/opt/airflow/data", num_samples=50, minio_endpoint="127.0.0.1:9000",
                             minio_access_key="admin", minio_secret_key="password",
                             raw_data_bucket="raw-data", new_sales_bucket="new-sales"):
    """
    Generate Onlinesales_new.csv with 50 random transactions based on merged_data.pkl.
    Downloads merged_data.pkl from MinIO raw_data bucket and uploads Onlinesales_new.csv to new_sales bucket.
    Saves the file locally in data_dir for compatibility.
    """
    import tempfile

    # Initialize MinIO client
    client = Minio(
        minio_endpoint,
        access_key=minio_access_key,
        secret_key=minio_secret_key,
        secure=False
    )

    # Download merged_data.pkl from MinIO
    merged_path = os.path.join(data_dir, "merged_data.pkl")
    os.makedirs(data_dir, exist_ok=True)
    try:
        client.fget_object(raw_data_bucket, "merged_data.pkl", merged_path)
        print(
            f"Downloaded merged_data.pkl from MinIO: {raw_data_bucket}/merged_data.pkl")
    except Exception as e:
        raise FileNotFoundError(
            f"Failed to download merged_data.pkl from MinIO: {e}")

    # Load merged_data.pkl
    merged_df = pd.read_pickle(merged_path)

    # Columns for Onlinesales_new.csv (based on original Onlinesales.csv)
    onlinesales_columns = [
        '고객ID', '거래ID', '거래날짜', '제품ID', '제품카테고리',
        '수량', '평균금액', '배송료', '쿠폰상태'
    ]

    # Initialize new DataFrame
    new_data = []

    # Get unique values for sampling
    unique_customers = merged_df['고객ID'].unique()
    unique_products = merged_df['제품ID'].unique()
    unique_categories = merged_df['제품카테고리'].unique()  # No new categories
    unique_coupon_status = merged_df['쿠폰상태'].unique()

    # Generate transaction IDs (unique)
    def extract_num(s):
        m = re.search(r'(\d+)$', str(s))
        return int(m.group(1)) if m else np.nan

    # ① 기존 max 계산 대체
    nums = merged_df['거래ID'].apply(extract_num).dropna()
    last_transaction_num = int(nums.max()) if not nums.empty else 0

    # Generate random transactions
    for i in range(num_samples):
        # Randomly sample values from existing data
        customer_id = np.random.choice(unique_customers)
        transaction_id = f"Transaction_{last_transaction_num + i + 1:04d}"
        product_id = np.random.choice(unique_products)
        category = np.random.choice(unique_categories)
        quantity = np.random.randint(1, 10)  # Random quantity between 1 and 10
        avg_amount = np.random.uniform(
            merged_df['평균금액'].min(),
            merged_df['평균금액'].max()
        )
        shipping_fee = np.random.uniform(
            merged_df['배송료'].min(),
            merged_df['배송료'].max()
        )
        coupon_status = np.random.choice(unique_coupon_status)

        # Generate a recent transaction date (within last 30 days)
        days_ago = np.random.randint(0, 30)
        transaction_date = (
            datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")

        new_data.append({
            '고객ID': customer_id,
            '거래ID': transaction_id,
            '거래날짜': transaction_date,
            '제품ID': product_id,
            '제품카테고리': category,
            '수량': quantity,
            '평균금액': avg_amount,
            '배송료': shipping_fee,
            '쿠폰상태': coupon_status
        })

    # Create DataFrame
    new_df = pd.DataFrame(new_data, columns=onlinesales_columns)

    # Apply CATEGORY_MAP to ensure consistency
    new_df['제품카테고리'] = new_df['제품카테고리'].map(
        CATEGORY_MAP).fillna(new_df['제품카테고리'])

    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp_file:
        temp_path = tmp_file.name
        new_df.to_csv(temp_path, index=False, encoding='utf-8-sig')
        print(f"Saved to temp file: {temp_path}")

    # # Save to Onlinesales_new.csv locally
    # output_path = os.path.join(data_dir, "Onlinesales_new.csv")
    # new_df.to_csv(output_path, index=False, encoding='utf-8-sig')
    # print(f"Saved Onlinesales_new.csv to {output_path}")

    # Upload to MinIO new_sales bucket
    try:
        client.fput_object(
            new_sales_bucket, "Onlinesales_new.csv", temp_path)
        print(
            f"Uploaded Onlinesales_new.csv to MinIO: {new_sales_bucket}/Onlinesales_new.csv")
    except Exception as e:
        print(f"Failed to upload Onlinesales_new.csv to MinIO: {e}")

    finally:
        # 임시 파일 삭제
        if os.path.exists(temp_path):
            os.remove(temp_path)

    return temp_path


if __name__ == "__main__":
    generate_new_onlinesales(
        data_dir="../data",
        num_samples=50,
        minio_endpoint="127.0.0.1:9000",
        minio_access_key="admin",
        minio_secret_key="password",
        raw_data_bucket="raw-data",
        new_sales_bucket="new-sales"
    )
