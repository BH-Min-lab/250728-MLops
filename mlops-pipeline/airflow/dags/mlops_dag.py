# mlops_dag.py - 최적화 버전
from __future__ import annotations
from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.providers.docker.operators.docker import DockerOperator
from airflow.operators.dummy import DummyOperator
from datetime import datetime, timedelta
import os
from omegaconf import OmegaConf
from minio import Minio
from minio.error import S3Error
from pathlib import Path
from docker.types import Mount
from generate_new_onlinesales import generate_new_onlinesales

# 설정 상수
CFG = OmegaConf.load("/opt/airflow/dags/config.yaml")
M_ENDPOINT = "minio:9000"
M_ACCESS = "admin"
M_SECRET = "password"
RAW_BUCKET = CFG.dataset.args.raw_data_bucket
NEW_BUCKET = CFG.dataset.args.new_sales_bucket
MODEL_BUCKET = CFG.dataset.args.models_bucket
LOCAL_DATA_DIR = "/opt/airflow/data"
NETWORK_NAME = "mlops-project-server-dl_airflow_mlflow_compose_default"
TRAIN_IMAGE = "mlops-project-server-dl_airflow_mlflow_compose-backendtrain:latest"
HOST = os.environ["HOST_PROJECT_ROOT"]


def ensure_buckets(**_):
    """버킷만 생성 (CSV 업로드는 초기 1회만)"""
    client = Minio(M_ENDPOINT, M_ACCESS, M_SECRET, secure=False)
    for b in (RAW_BUCKET, NEW_BUCKET, MODEL_BUCKET):
        if not client.bucket_exists(b):
            client.make_bucket(b)
            print(f"Created bucket: {b}")


def check_and_upload_csv(**context):
    """CSV 파일이 MinIO에 없을 때만 업로드"""
    client = Minio(M_ENDPOINT, M_ACCESS, M_SECRET, secure=False)
    csvs = [
        "Customer_info.csv", "Discount_info.csv",
        "Marketing_info.csv", "Onlinesales_info.csv", "Tax_info.csv",
    ]

    uploaded = False
    for f in csvs:
        try:
            client.stat_object(RAW_BUCKET, f)
        except S3Error:
            # 파일이 없을 때만 업로드
            abs_path = f"{LOCAL_DATA_DIR}/{f}"
            if os.path.exists(abs_path):
                client.fput_object(RAW_BUCKET, f, abs_path)
                print(f"Uploaded {f} to MinIO")
                uploaded = True
            else:
                raise FileNotFoundError(f"{abs_path} not found")

    # Context에 플래그 저장
    context['task_instance'].xcom_push(key='csv_uploaded', value=uploaded)
    return 'branch_by_merged_file' if uploaded or context['dag_run'].run_id.startswith('scheduled') else 'skip_initial'


def _branch_by_merged_file(**_):
    """merged_data.pkl 존재 여부로 분기"""
    client = Minio(M_ENDPOINT, M_ACCESS, M_SECRET, secure=False)
    try:
        client.stat_object(RAW_BUCKET, "merged_data.pkl")
        return "generate_new_onlinesales"  # 정규 사이클
    except S3Error:
        return "initial_merge"  # 초기 병합


def merge_and_preprocess(config, use_new_sales=True, **_):
    from dataset import make_features
    data_dir = config.dataset.args.data_dir
    new_sales = config.dataset.args.new_onlinesales_path if use_new_sales else None

    make_features(
        in_columns=[
            '고객ID', '거래ID', '거래날짜', '제품ID', '제품카테고리', '수량',
            '평균금액', '배송료', '쿠폰상태', '성별', '고객지역', '가입기간',
            'GST', '월', '쿠폰코드', '할인율', '거래금액'
        ],
        out_columns=['제품카테고리'],
        is_training=True,
        data_dir=data_dir,
        new_onlinesales_path=new_sales,
        minio_endpoint=M_ENDPOINT,
        minio_access_key=M_ACCESS,
        minio_secret_key=M_SECRET,
        raw_data_bucket=RAW_BUCKET,
        new_sales_bucket=NEW_BUCKET,
    )


# DAG 정의
default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=1),
}

with DAG(
    dag_id="mlops_pipeline",
    start_date=datetime(2025, 8, 5, 0, 0),
    schedule_interval="*/3 * * * *",
    catchup=False,
    default_args=default_args,
    tags=["mlops"],
    max_active_runs=1,  # 동시 실행 방지
) as dag:

    # 1. 버킷 확인 (매번 실행 - 가벼운 작업)
    ensure_buckets_task = PythonOperator(
        task_id="ensure_buckets",
        python_callable=ensure_buckets,
    )

    # 2. CSV 업로드 체크 (필요시만)
    check_csv_task = BranchPythonOperator(
        task_id="check_and_upload_csv",
        python_callable=check_and_upload_csv,
    )

    # 3. 스킵 더미 (CSV 이미 있을 때)
    skip_initial = DummyOperator(
        task_id="skip_initial"
    )

    # 4. 분기 결정
    branch_task = BranchPythonOperator(
        task_id="branch_by_merged_file",
        python_callable=_branch_by_merged_file,
        trigger_rule="none_failed_or_skipped",
    )

    TRAIN_MOUNTS = [
        Mount(source=f"{HOST}/backendTrain/src",
              target="/app/src", type="bind", read_only=False),
        Mount(source=f"{HOST}/backendTrain/data",
              target="/opt/airflow/data", type="bind"),
        Mount(source="minio_artifacts",
              target="/ml-artifacts", type="volume"),
    ]

    # 초기 병합 & 학습
    initial_merge = PythonOperator(
        task_id="initial_merge",
        python_callable=merge_and_preprocess,
        op_kwargs={"config": CFG, "use_new_sales": False},
    )

    initial_train = DockerOperator(
        task_id="initial_train",
        image=TRAIN_IMAGE,
        command="python src/train.py --config src/config.yaml --mode train",
        network_mode=NETWORK_NAME,
        mounts=TRAIN_MOUNTS,
        mount_tmp_dir=False,
        auto_remove=True,
        environment={
            "SAVE_DIR": "/ml-artifacts",
            "MLFLOW_TRACKING_URI": "http://mlflow:5000",
            "AWS_ACCESS_KEY_ID": "admin",
            "AWS_SECRET_ACCESS_KEY": "password",
            "MLFLOW_S3_ENDPOINT_URL": "http://minio:9000"
        },
    )

    # 정규 사이클
    generate_task = PythonOperator(
        task_id="generate_new_onlinesales",
        python_callable=generate_new_onlinesales,
        op_kwargs=dict(
            data_dir='/opt/airflow/data',
            num_samples=50,
            minio_endpoint=M_ENDPOINT,
            minio_access_key=M_ACCESS,
            minio_secret_key=M_SECRET,
            raw_data_bucket=RAW_BUCKET,
            new_sales_bucket=NEW_BUCKET,
        ),
    )

    merge_task = PythonOperator(
        task_id="merge_and_preprocess",
        python_callable=merge_and_preprocess,
        op_kwargs={"config": CFG, "use_new_sales": True},
    )

    regular_train = DockerOperator(
        task_id="train_model",
        image=TRAIN_IMAGE,
        command="python src/train.py --config src/config.yaml --mode train",
        network_mode=NETWORK_NAME,
        mounts=TRAIN_MOUNTS,
        mount_tmp_dir=False,
        auto_remove=True,
        environment={
            "SAVE_DIR": "/ml-artifacts",
            "MLFLOW_TRACKING_URI": "http://mlflow:5000",
            "AWS_ACCESS_KEY_ID": "admin",
            "AWS_SECRET_ACCESS_KEY": "password",
            "MLFLOW_S3_ENDPOINT_URL": "http://minio:9000"
        },
    )

    # 의존성 설정
    ensure_buckets_task >> check_csv_task
    check_csv_task >> [skip_initial, branch_task]
    skip_initial >> branch_task

    branch_task >> initial_merge >> initial_train
    branch_task >> generate_task >> merge_task >> regular_train
