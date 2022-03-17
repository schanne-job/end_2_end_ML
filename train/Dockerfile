FROM python:3.8-slim

ARG http_proxy=http://host.docker.internal:3128
ARG https_proxy=http://host.docker.internal:3128
ARG no_proxy=127.0.0.1,localhost,.bosch.com

RUN apt-get update
RUN apt-get -y install git
RUN pip install mlflow boto3 pymysql minio sklearn cryptography

WORKDIR /training
COPY ./kc_house_data.csv .
COPY ./train.py .

CMD tail -f /dev/null
#CMD python train.py