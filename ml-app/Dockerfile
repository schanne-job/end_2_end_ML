FROM python:3.6

ARG http_proxy=http://host.docker.internal:3128
ARG https_proxy=http://host.docker.internal:3128
ARG no_proxy=127.0.0.1,localhost,.bosch.com

WORKDIR /app
COPY ./requirements.txt /app
RUN pip install -r requirements.txt

COPY . /app

EXPOSE 5000
ENV MODEL_NAME Model
ENV API_TYPE REST 
ENV SERVICE_TYPE MODEL
ENV PERSISTANCE 0

CMD exec seldon-core-microservice ${MODEL_NAME} ${API_TYPE} --service-type ${SERVICE_TYPE}