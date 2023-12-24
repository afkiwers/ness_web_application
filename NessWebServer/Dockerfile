# pull official base image
FROM python:3.9.0-alpine3.12

#FROM debian:wheezy

# When this Dockerfile was last refreshed
ENV REFRESHED_AT 2020-04-04

# set environment varibles
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV NESS_WEB_SERVER_DIR=/NessWebServer

ENV LIBRARY_PATH=/lib:/usr/lib

RUN mkdir -p /var/log/gunicorn
RUN mkdir -p /var/log/crontab

RUN mkdir $NESS_WEB_SERVER_DIR

# set work directory
WORKDIR $NESS_WEB_SERVER_DIR

ADD requirements.txt $NESS_WEB_SERVER_DIR/

RUN apk add --no-cache mariadb-dev build-base

RUN apk --no-cache add --virtual build-dependencies \
    build-base \
    gcc \
    libc-dev \
    libffi-dev \
	py-pip\
    jpeg-dev\
	zlib-dev \
	python3-dev \
    && pip install -r requirements.txt

ADD . $NESS_WEB_SERVER_DIR/

# copy entrypoint.sh
COPY ./entrypoint.sh ./entrypoint.sh

# run entrypoint.sh
ENTRYPOINT ["./entrypoint.sh"]
