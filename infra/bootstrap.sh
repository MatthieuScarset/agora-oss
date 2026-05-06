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

  log_info "Ensuring PostgreSQL schemas and pgvector extension exist..."
  if docker compose -f "$PROJECT_ROOT/docker-compose.yml" --env-file "$PROJECT_ROOT/.env" exec -T postgres \
    psql -U "${POSTGRES_USER:-agora}" -d "${POSTGRES_DB:-agora}" -v ON_ERROR_STOP=1 \
    -c "CREATE SCHEMA IF NOT EXISTS public; CREATE SCHEMA IF NOT EXISTS prefect; CREATE EXTENSION IF NOT EXISTS vector SCHEMA public;" >/dev/null 2>&1; then
    log_info "PostgreSQL schema repair check completed"
  else
    log_warn "Unable to precreate PostgreSQL schemas or pgvector extension; continuing to poll"
  fi

  while [ $attempt -lt $max_attempts ]; do
    log_info "Checking PostgreSQL + pgvector (attempt $((attempt + 1))/${max_attempts})..."
    if docker compose -f "$PROJECT_ROOT/docker-compose.yml" --env-file "$PROJECT_ROOT/.env" exec -T postgres \
      psql -U "${POSTGRES_USER:-agora}" -d "${POSTGRES_DB:-agora}" \
      -Atqc "SELECT extname FROM pg_extension WHERE extname = 'vector';" | grep -qx vector; then
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

# Check and install MinIO client if needed
check_minio_client() {
  local minio_client_url="https://dl.min.io/client/mc/release/linux-amd64/mc"

  # Check if minio-mc is already installed
  if which minio-mc >/dev/null 2>&1; then
    log_info "MinIO client is already installed"
    return 0
  fi

  # MinIO client not found
  log_warn "MinIO client is not installed"
  echo ""
  echo "The MinIO client is required to bootstrap MinIO."
  echo "Download URL: $minio_client_url"
  echo ""
  read -p "Would you like to install MinIO client now? (y/n) " -n 1 -r
  echo ""

  if [[ $REPLY =~ ^[Yy]$ ]]; then
    log_info "Installing MinIO client..."
    mkdir -p ~/.local/bin
    curl -L -o ~/.local/bin/minio-mc "$minio_client_url" || { log_error "Failed to download MinIO client"; exit 1; }
    chmod +x ~/.local/bin/minio-mc || { log_error "Failed to make MinIO client executable"; exit 1; }

    # Verify installation
    if which minio-mc >/dev/null 2>&1; then
      log_info "MinIO client installed successfully"
      return 0
    else
      log_error "MinIO client not found in PATH. Please add ~/.local/bin to your PATH."
      exit 1
    fi
  else
    log_error "MinIO client is required. Please install from: $minio_client_url"
    exit 1
  fi
}

# Bootstrap MinIO bucket
bootstrap_minio() {
  log_info "Bootstrapping MinIO bucket..."

  # Check and ensure MinIO client is available
  check_minio_client

  local bucket="${S3_BUCKET:-agora-raw}"
  local endpoint="http://localhost:${MINIO_API_PORT:-9000}"

  log_info "Configuring MinIO client alias..."
  if ! timeout 15s minio-mc alias set local "$endpoint" "${MINIO_ROOT_USER}" "${MINIO_ROOT_PASSWORD}" >/dev/null 2>&1; then
    log_error "Failed to configure MinIO client alias for ${endpoint}"
    exit 1
  fi

  log_info "Creating MinIO bucket: ${bucket}"
  if ! timeout 15s minio-mc mb --ignore-existing "local/${bucket}" >/dev/null 2>&1; then
    log_error "Failed to create MinIO bucket: ${bucket}"
    exit 1
  fi

  log_info "MinIO bootstrap completed (bucket: ${bucket})"
  return 0
}

# Wait for Redis
wait_redis() {
  log_info "Waiting for Redis..."

  local max_attempts=60
  local attempt=0

  while [ $attempt -lt $max_attempts ]; do
    log_info "Checking Redis (attempt $((attempt + 1))/${max_attempts})..."
    if docker compose -f "$PROJECT_ROOT/docker-compose.yml" --env-file "$PROJECT_ROOT/.env" exec -T redis \
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
    log_warn "prefect CLI not found. Did you actived the virtual env? "source .venv/bin/activate""
    log_warn "Skipping Prefect bootstrap"
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

# Display service URLs
display_service_urls() {
  echo ""
  echo "=========================================="
  echo "Service URLs:"
  echo "=========================================="
  echo "Prefect UI:      http://localhost:${PREFECT_API_PORT:-4200}"
  echo "MinIO Console:   http://localhost:${MINIO_CONSOLE_PORT:-9001}"
  echo "Frontend:        http://localhost:${FRONTEND_PORT:-3000}"
  echo "Redis:           localhost:${REDIS_PORT:-6379}"
  echo "PostgreSQL:      localhost:${POSTGRES_PORT:-5432}"
  echo "=========================================="
  echo ""
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
  display_service_urls
}

# Only run main if script is executed directly (not sourced)
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  main "$@"
fi
