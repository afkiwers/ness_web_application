# Use a stable, lightweight Debian-based Python image
FROM python:3.11.7-slim

# Set working directory
WORKDIR /app

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
        && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your app code and entrypoint script
COPY . .

# Convert entrypoint.sh to Unix format (optional safety)
RUN sed -i 's/\r$//' ./entrypoint.sh && chmod +x ./entrypoint.sh

# Set entrypoint
ENTRYPOINT ["./entrypoint.sh"]
