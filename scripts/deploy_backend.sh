#!/usr/bin/env bash

set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-/opt/web-backend-python/web-backend-python}"
BRANCH="${BRANCH:-main}"
SERVICE_NAME="${SERVICE_NAME:-backend}"
CONTAINER_NAME="${CONTAINER_NAME:-ultra-ai-backend}"
DOCKER_COMPOSE_BIN="${DOCKER_COMPOSE_BIN:-docker compose}"

echo "[deploy] project dir: ${PROJECT_DIR}"
echo "[deploy] branch: ${BRANCH}"
echo "[deploy] service: ${SERVICE_NAME}"

cd "${PROJECT_DIR}"

echo "[deploy] git fetch"
git fetch origin "${BRANCH}"

CURRENT_BRANCH="$(git branch --show-current)"
if [ "${CURRENT_BRANCH}" != "${BRANCH}" ]; then
  echo "[deploy] checkout ${BRANCH}"
  git checkout "${BRANCH}"
fi

echo "[deploy] git pull --ff-only"
git pull --ff-only origin "${BRANCH}"

echo "[deploy] docker compose build ${SERVICE_NAME}"
${DOCKER_COMPOSE_BIN} build "${SERVICE_NAME}"

echo "[deploy] run migrations in one-off container"
${DOCKER_COMPOSE_BIN} run --rm "${SERVICE_NAME}" python3 migrate.py

echo "[deploy] recreate ${SERVICE_NAME}"
${DOCKER_COMPOSE_BIN} up -d --force-recreate "${SERVICE_NAME}"

echo "[deploy] wait for container to become ready"
sleep 5

echo "[deploy] backend container status"
docker ps --filter "name=${CONTAINER_NAME}"

echo "[deploy] recent logs"
${DOCKER_COMPOSE_BIN} logs --tail=80 "${SERVICE_NAME}"

echo "[deploy] done"
