# pull official base image
FROM python:3.7-alpine
#FROM debian:wheezy

# When this Dockerfile was last refreshed
ENV REFRESHED_AT 2020-04-04

# set environment varibles
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV WEBAPP_DIR=/webapp

ENV LIBRARY_PATH=/lib:/usr/lib

RUN mkdir -p /var/log/gunicorn
RUN mkdir -p /var/log/crontab

RUN mkdir $WEBAPP_DIR

# set work directory
WORKDIR $WEBAPP_DIR

ADD requirements.txt $WEBAPP_DIR/

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
#	libmysqlclient-dev \
#	libssl-dev \
#	libmariadbclient-dev \
#	libssl-dev\
    && pip install -r requirements.txt

ADD . $WEBAPP_DIR/

# copy entrypoint.sh
COPY ./entrypoint.sh ./entrypoint.sh

# run entrypoint.sh
ENTRYPOINT ["./entrypoint.sh"]
