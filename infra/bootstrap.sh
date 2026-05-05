#!/usr/bin/env bash
set -euo pipefail

# Central bootstrap orchestrator for Agora infrastructure
# Handles PostgreSQL + pgvector, MinIO, Prefect, and smoke tests

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Load environment variables
if [ -f "$PROJECT_ROOT/.env" ]; then
  set -a
  # shellcheck source=/dev/null
  source "$PROJECT_ROOT/.env"
  set +a
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
  echo -e "${GREEN}[INFO]${NC} $*"
}

log_warn() {
  echo -e "${YELLOW}[WARN]${NC} $*"
}

log_error() {
  echo -e "${RED}[ERROR]${NC} $*"
}

# Verify Docker Compose is available and stack is running
verify_docker_stack() {
  log_info "Verifying Docker Compose stack..."

  if ! command -v docker >/dev/null 2>&1; then
    log_error "docker is required but not found"
    exit 1
  fi

  if ! docker compose -f "$PROJECT_ROOT/docker-compose.yml" --env-file "$PROJECT_ROOT/.env" ps >/dev/null 2>&1; then
    log_error "Docker Compose stack is not reachable. Run: make docker-up"
    exit 1
  fi

  log_info "Docker Compose stack is running"
}

# Wait for PostgreSQL and pgvector extension
wait_postgres() {
  log_info "Waiting for PostgreSQL with pgvector..."

  local max_attempts=60
  local attempt=0

  while [ $attempt -lt $max_attempts ]; do
    if docker compose -f "$PROJECT_ROOT/docker-compose.yml" --env-file "$PROJECT_ROOT/.env" exec postgres \
      psql -U "${POSTGRES_USER:-agora}" -d "${POSTGRES_DB:-agora}" \
      -c "SELECT extname FROM pg_extension WHERE extname = 'vector';" >/dev/null 2>&1 | grep -q vector; then
      log_info "PostgreSQL with pgvector is ready"
      return 0
    fi

    attempt=$((attempt + 1))
    sleep 1
  done

  log_error "PostgreSQL with pgvector failed to initialize"
  exit 1
}

# Wait for MinIO to be healthy
wait_minio() {
  log_info "Waiting for MinIO..."

  local max_attempts=60
  local attempt=0

  while [ $attempt -lt $max_attempts ]; do
    if curl -fsS "http://localhost:${MINIO_API_PORT:-9000}/minio/health/live" >/dev/null 2>&1; then
      log_info "MinIO is ready"
      return 0
    fi

    attempt=$((attempt + 1))
    sleep 1
  done

  log_error "MinIO failed to become healthy"
  exit 1
}

# Bootstrap MinIO bucket
bootstrap_minio() {
  log_info "Bootstrapping MinIO bucket..."

  local bucket="${S3_BUCKET:-agora-raw}"
  local max_attempts=30
  local attempt=0

  # Configure MinIO alias and create bucket
  while [ $attempt -lt $max_attempts ]; do
    if mc alias set local "http://localhost:${MINIO_API_PORT:-9000}" "${MINIO_ROOT_USER}" "${MINIO_ROOT_PASSWORD}" >/dev/null 2>&1; then
      mc mb --ignore-existing "local/${bucket}" 2>/dev/null || true
      log_info "MinIO bootstrap completed (bucket: ${bucket})"
      return 0
    fi

    attempt=$((attempt + 1))
    sleep 2
  done

  log_error "Failed to bootstrap MinIO bucket"
  exit 1
}

# Wait for Redis
wait_redis() {
  log_info "Waiting for Redis..."

  local max_attempts=60
  local attempt=0

  while [ $attempt -lt $max_attempts ]; do
    if docker compose -f "$PROJECT_ROOT/docker-compose.yml" --env-file "$PROJECT_ROOT/.env" exec redis \
      redis-cli ping >/dev/null 2>&1; then
      log_info "Redis is ready"
      return 0
    fi

    attempt=$((attempt + 1))
    sleep 1
  done

  log_error "Redis failed to become healthy"
  exit 1
}

# Bootstrap Prefect work pool
bootstrap_prefect() {
  log_info "Bootstrapping Prefect work pool..."

  if ! command -v prefect >/dev/null 2>&1; then
    log_warn "prefect CLI not found, skipping Prefect bootstrap"
    return
  fi

  local work_pool="${PREFECT_WORK_POOL:-agora-local-pool}"

  if prefect work-pool inspect "${work_pool}" >/dev/null 2>&1; then
    log_info "Prefect work pool already exists: ${work_pool}"
  else
    log_info "Creating Prefect work pool: ${work_pool}"
    prefect work-pool create "${work_pool}" --type process
  fi

  log_info "Prefect bootstrap completed"
}

# Run smoke tests (health checks)
run_smoke_tests() {
  log_info "Running smoke tests and health checks..."

  log_info "Checking required services are running..."
  local required_services=(postgres redis minio prefect-server prefect-worker)
  for svc in "${required_services[@]}"; do
    local state
    state=$(docker compose -f "$PROJECT_ROOT/docker-compose.yml" --env-file "$PROJECT_ROOT/.env" ps --format json "$svc" 2>/dev/null | tr -d '\n')
    if [[ "$state" != *"\"State\":\"running\""* ]]; then
      log_error "Service $svc is not running"
      exit 1
    fi
    log_info "✓ $svc is running"
  done

  log_info "Checking PostgreSQL + pgvector..."
  if docker compose -f "$PROJECT_ROOT/docker-compose.yml" --env-file "$PROJECT_ROOT/.env" exec postgres \
    psql -U "${POSTGRES_USER:-agora}" -d "${POSTGRES_DB:-agora}" \
    -c "SELECT extname FROM pg_extension WHERE extname = 'vector';" >/dev/null 2>&1; then
    log_info "✓ PostgreSQL + pgvector is healthy"
  else
    log_error "PostgreSQL + pgvector check failed"
    exit 1
  fi

  log_info "Checking Redis..."
  if docker compose -f "$PROJECT_ROOT/docker-compose.yml" --env-file "$PROJECT_ROOT/.env" exec redis \
    redis-cli ping >/dev/null 2>&1; then
    log_info "✓ Redis is healthy"
  else
    log_error "Redis check failed"
    exit 1
  fi

  log_info "Checking MinIO health endpoint..."
  if ! curl -fsS "http://localhost:${MINIO_API_PORT:-9000}/minio/health/live" >/dev/null 2>&1; then
    log_error "MinIO health endpoint failed"
    exit 1
  fi
  log_info "✓ MinIO is healthy"

  log_info "Checking Prefect API health endpoint..."
  if ! curl -fsS "http://localhost:${PREFECT_API_PORT:-4200}/api/health" >/dev/null 2>&1; then
    log_error "Prefect API health endpoint failed"
    exit 1
  fi
  log_info "✓ Prefect API is healthy"

  log_info "Checking Frontend endpoint..."
  if curl -fsS "http://localhost:${FRONTEND_PORT:-3000}" >/dev/null 2>&1; then
    log_info "✓ Frontend endpoint is reachable"
  else
    log_warn "Frontend endpoint not reachable yet (expected if dashboard app is not created)"
  fi

  log_info "✓ All smoke checks completed successfully"
}

# Main orchestration
main() {
  log_info "Starting Agora infrastructure bootstrap..."

  verify_docker_stack
  wait_postgres
  wait_redis
  wait_minio
  bootstrap_minio
  bootstrap_prefect

  log_info "Running health checks..."
  run_smoke_tests

  log_info "✓ All infrastructure bootstrapped successfully!"
}

# Only run main if script is executed directly (not sourced)
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  main "$@"
fi
