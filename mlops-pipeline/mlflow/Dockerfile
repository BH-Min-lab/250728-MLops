# mlflow/Dockerfile
FROM python:3.11-slim

RUN apt-get update && \
    apt-get install -y curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    mlflow==2.10.0 \
    boto3==1.34.0 \
    pymysql==1.1.0

WORKDIR /mlflow

EXPOSE 5000

CMD ["mlflow", "server", \
    "--host", "0.0.0.0", \
    "--port", "5000", \
    "--backend-store-uri", "sqlite:////mlflow/mlflow.db", \
    "--default-artifact-root", "/mlflow/artifacts"]