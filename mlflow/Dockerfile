FROM python:3.8-slim

ARG http_proxy=http://host.docker.internal:3128
ARG https_proxy=http://host.docker.internal:3128
ARG no_proxy=127.0.0.1,localhost,.bosch.com

RUN pip install mlflow boto3 pymysql minio sklearn cryptography

# mlflow server is started in docker compose!