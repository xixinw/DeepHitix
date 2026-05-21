#!/usr/bin/env bash
set -euo pipefail

# DeepSeek Native Agent Linux installer
#
# This installer wires the Docker Compose validation base into a repeatable
# Linux user-service deployment. It does not install Docker automatically; that
# remains an explicit prerequisite to avoid distro-specific side effects.

PROJECT_NAME="deepseek-native-agent"
DEFAULT_INSTALL_DIR="${HOME}/deepseek-native-agent"
INSTALL_DIR="${INSTALL_DIR:-$DEFAULT_INSTALL_DIR}"
SERVICE_NAME="deepseek-native-agent.service"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
DEPLOY_DIR="${PROJECT_ROOT}/deploy"
ENV_FILE="${DEPLOY_DIR}/.env"
ENV_EXAMPLE="${DEPLOY_DIR}/.env.example"
SERVICE_DIR="${HOME}/.config/systemd/user"
SERVICE_PATH="${SERVICE_DIR}/${SERVICE_NAME}"

usage() {
  cat <<'EOF'
Usage: deploy/install.sh [--install-dir PATH] [--write-service-only]

Environment variables:
  DEEPSEEK_API_KEY       Required for first-time .env generation unless deploy/.env exists.
  API_SERVER_KEY         Optional; generated automatically if missing.
  INSTALL_DIR            Install directory used by the systemd unit. Default: ~/deepseek-native-agent

Examples:
  DEEPSEEK_API_KEY=sk-... deploy/install.sh
  INSTALL_DIR=/opt/deepseek-native-agent DEEPSEEK_API_KEY=sk-... deploy/install.sh
  deploy/install.sh --write-service-only

After install:
  systemctl --user status deepseek-native-agent
  journalctl --user -u deepseek-native-agent -f
EOF
}

WRITE_SERVICE_ONLY=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --install-dir)
      INSTALL_DIR="${2:?--install-dir requires a path}"
      shift 2
      ;;
    --write-service-only)
      WRITE_SERVICE_ONLY=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "Missing required command: $1" >&2
    exit 1
  }
}

ensure_prereqs() {
  need_cmd docker
  docker compose version >/dev/null 2>&1 || {
    echo "Missing required command: docker compose" >&2
    exit 1
  }
  need_cmd systemctl
  need_cmd python3
}

generate_key() {
  if command -v openssl >/dev/null 2>&1; then
    openssl rand -hex 32
  else
    python3 - <<'PY'
import secrets
print(secrets.token_hex(32))
PY
  fi
}

write_env_if_needed() {
  if [[ -f "$ENV_FILE" ]]; then
    echo "Using existing ${ENV_FILE}"
    return
  fi
  [[ -f "$ENV_EXAMPLE" ]] || {
    echo "Missing ${ENV_EXAMPLE}" >&2
    exit 1
  }
  if [[ -z "${DEEPSEEK_API_KEY:-}" ]]; then
    echo "DEEPSEEK_API_KEY is required for first-time deploy/.env generation." >&2
    echo "Pass it as an environment variable or create ${ENV_FILE} manually." >&2
    exit 1
  fi
  local api_server_key="${API_SERVER_KEY:-$(generate_key)}"
  cp "$ENV_EXAMPLE" "$ENV_FILE"
  python3 - "$ENV_FILE" "$DEEPSEEK_API_KEY" "$api_server_key" <<'PY'
from pathlib import Path
import sys
path = Path(sys.argv[1])
deepseek_key = sys.argv[2]
api_key = sys.argv[3]
text = path.read_text(encoding='utf-8')
text = text.replace('DEEPSEEK_API_KEY=\n', f'DEEPSEEK_API_KEY={deepseek_key}\n')
text = text.replace('API_SERVER_KEY=\n', f'API_SERVER_KEY={api_key}\n')
path.write_text(text, encoding='utf-8')
PY
  chmod 600 "$ENV_FILE" || true
  echo "Created ${ENV_FILE}"
}

write_service() {
  mkdir -p "$SERVICE_DIR"
  cat > "$SERVICE_PATH" <<EOF
[Unit]
Description=DeepSeek Native Agent Docker Compose gateway
After=network-online.target docker.service
Wants=network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=${DEPLOY_DIR}
ExecStart=/usr/bin/docker compose --env-file ${ENV_FILE} up -d
ExecStop=/usr/bin/docker compose --env-file ${ENV_FILE} down
TimeoutStartSec=180
TimeoutStopSec=120

[Install]
WantedBy=default.target
EOF
  echo "Wrote ${SERVICE_PATH}"
}

validate_compose() {
  python3 "${DEPLOY_DIR}/validate_compose.py"
  docker compose --env-file "$ENV_FILE" -f "${DEPLOY_DIR}/docker-compose.yml" config >/dev/null
  echo "Docker Compose config validation passed"
}

build_image() {
  # Build the thin DeepSeek-native image layer before service start so Feishu
  # optional dependencies are present without manual in-container installs.
  docker compose --env-file "$ENV_FILE" -f "${DEPLOY_DIR}/docker-compose.yml" build deepseek-native-agent
  echo "Docker image build passed"
}

write_runtime_config_if_needed() {
  # The upstream Hermes container bootstraps a generic config.yaml when the
  # mounted data directory is empty.  For the DeepSeek-native deployment base we
  # must materialize a small runtime config before first boot; otherwise gateway
  # agents can inherit the image default model while using the DeepSeek provider.
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a

  local data_dir="${DEEPSEEK_NATIVE_DATA_DIR:-./data}"
  if [[ "$data_dir" != /* ]]; then
    data_dir="${DEPLOY_DIR}/${data_dir}"
  fi
  mkdir -p "$data_dir"

  local config_file="${data_dir}/config.yaml"
  if [[ -f "$config_file" ]]; then
    echo "Using existing ${config_file}"
    return
  fi

  local provider="${HERMES_INFERENCE_PROVIDER:-${HERMES_PROVIDER:-deepseek}}"
  local model="${HERMES_MODEL:-deepseek-v4-flash}"
  local flash_model="${DEEPSEEK_NATIVE_FLASH_MODEL:-deepseek-v4-flash}"
  local pro_model="${DEEPSEEK_NATIVE_PRO_MODEL:-deepseek-v4-pro}"

  cat > "$config_file" <<EOF
# Generated by deploy/install.sh for DeepSeek Native Agent.
# Secrets remain in deploy/.env; do not put API keys in this file.
model:
  provider: "${provider}"
  default: "${model}"

deepseek_native:
  routing:
    enabled: ${DEEPSEEK_NATIVE_ROUTING_ENABLED:-true}
    flash_model: "${flash_model}"
    pro_model: "${pro_model}"
  telemetry:
    enabled: ${DEEPSEEK_NATIVE_TELEMETRY_ENABLED:-true}

gateway:
  platform_toolsets:
    api_server: [hermes-api-server]
    feishu: [hermes-feishu]
EOF
  chmod 600 "$config_file" || true
  echo "Created ${config_file}"
}

start_service() {
  systemctl --user daemon-reload
  systemctl --user enable "$SERVICE_NAME"
  systemctl --user restart "$SERVICE_NAME"
  systemctl --user --no-pager status "$SERVICE_NAME" || true
}

main() {
  ensure_prereqs

  if [[ "$PROJECT_ROOT" != "$INSTALL_DIR" ]]; then
    mkdir -p "$(dirname "$INSTALL_DIR")"
    if [[ ! -d "$INSTALL_DIR" ]]; then
      cp -a "$PROJECT_ROOT" "$INSTALL_DIR"
      echo "Copied project to ${INSTALL_DIR}"
      echo "Re-run from ${INSTALL_DIR}/deploy/install.sh to start service."
      exit 0
    fi
  fi

  write_env_if_needed
  write_runtime_config_if_needed
  write_service
  validate_compose
  build_image

  if [[ "$WRITE_SERVICE_ONLY" == "1" ]]; then
    echo "Service file written and image built; not starting service."
    exit 0
  fi

  start_service
  cat <<EOF

DeepSeek Native Agent service installed.

Useful commands:
  systemctl --user status ${SERVICE_NAME}
  journalctl --user -u ${SERVICE_NAME} -f
  cd ${DEPLOY_DIR} && docker compose --env-file .env logs -f deepseek-native-agent

If this is a headless cloud VM and user services stop after logout, run once:
  sudo loginctl enable-linger "$USER"
EOF
}

main "$@"
