# ====== airflow/Dockerfile ======
FROM apache/airflow:2.8.1-python3.11

USER root               
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

USER airflow            

# 기존 패키지 + MLflow
RUN pip install --no-cache-dir \
    numpy==1.26.4 \
    pandas==2.2.0 \
    mlflow==2.10.0 \
    boto3==1.34.0

RUN pip install --no-cache-dir \
    torch==2.1.0+cpu \
    torchvision==0.16.0+cpu \
    --extra-index-url https://download.pytorch.org/whl/cpu

RUN pip install --no-cache-dir \
    scikit-learn==1.3.0 \
    joblib==1.3.2 \
    omegaconf==2.3.0 \
    minio==7.2.5