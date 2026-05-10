# Use a stable, Debian-based Python image
FROM python:3.11.7-slim

# Set working directory
WORKDIR /app

# Prevent interactive prompts during install
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
        libc-dev \
        libffi-dev \
        libjpeg-dev \
        zlib1g-dev \
        python3-dev \
        python3-pip \
        default-libmysqlclient-dev \
        pkg-config \
        curl \
        dos2unix \
        && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Normalise entrypoint (handle CRLF and permissions)
RUN dos2unix ./entrypoint.sh && chmod +x ./entrypoint.sh

# Git metadata baked in at build time by deploy-on-server.sh
ARG NESS_GIT_TAG=""
ARG NESS_GIT_BRANCH=""
ARG NESS_GIT_COMMIT=""
ARG NESS_GIT_COMMIT_DATE=""
ENV NESS_GIT_TAG=$NESS_GIT_TAG
ENV NESS_GIT_BRANCH=$NESS_GIT_BRANCH
ENV NESS_GIT_COMMIT=$NESS_GIT_COMMIT
ENV NESS_GIT_COMMIT_DATE=$NESS_GIT_COMMIT_DATE

# Set entrypoint
ENTRYPOINT ["./entrypoint.sh"]
