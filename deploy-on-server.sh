#!/bin/bash
set -e

# ── Configure these ────────────────────────────────────────────────────────────
SERVER_HOST="192.168.10.8"
SERVER_USER="afkiwers"
SERVER_PATH="/volume1/docker/ness2web"
PROJECT_NAME="ness_web"
# ──────────────────────────────────────────────────────────────────────────────

TAR_FILE="/tmp/${PROJECT_NAME}-images.tar"

GIT_TAG=$(git tag --merged HEAD --sort=-creatordate | head -n 1 || true)
GIT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || true)
GIT_COMMIT=$(git rev-parse HEAD 2>/dev/null || true)
GIT_COMMIT_DATE=$(git log -1 --date=format:%Y-%m-%d --pretty=format:%cd 2>/dev/null || true)
export NESS_GIT_TAG="$GIT_TAG"
export NESS_GIT_BRANCH="$GIT_BRANCH"
export NESS_GIT_COMMIT="$GIT_COMMIT"
export NESS_GIT_COMMIT_DATE="$GIT_COMMIT_DATE"

echo "[1/5] Building images..."
docker compose --project-name "$PROJECT_NAME" build django nginx

echo "[2/5] Saving images to $TAR_FILE..."
docker save -o "$TAR_FILE" \
  ness_web:django \
  ness_web:nginx

echo "[3/5] Transferring to Synology ($(du -sh "$TAR_FILE" | cut -f1))..."
ssh "${SERVER_USER}@${SERVER_HOST}" "mkdir -p ${SERVER_PATH}"
scp -O "$TAR_FILE" "${SERVER_USER}@${SERVER_HOST}:${SERVER_PATH}/"
scp -O docker-compose.synology.yml "${SERVER_USER}@${SERVER_HOST}:${SERVER_PATH}/"
scp -O .env "${SERVER_USER}@${SERVER_HOST}:${SERVER_PATH}/"

echo "[4/5] Loading images and restarting on Synology..."
ssh "${SERVER_USER}@${SERVER_HOST}" bash <<EOF
  set -e
  export PATH="\$PATH:/usr/local/bin:/var/packages/ContainerManager/target/bin:/var/packages/Docker/target/usr/bin"
  docker load -i "${SERVER_PATH}/$(basename "$TAR_FILE")"
  cd "${SERVER_PATH}"
  docker compose -f docker-compose.synology.yml up -d --force-recreate --remove-orphans
  docker compose -f docker-compose.synology.yml ps
EOF

echo "[5/5] Cleaning up local tar..."
rm "$TAR_FILE"

echo "Done. Ness is live on the Synology."
