#!/usr/bin/env bash
set -euo pipefail

# Run a Docker Compose smoke against a registry-published image.
# This script intentionally uses --no-build and --pull never after docker pull.
#
# Required environment:
#   DEEPSEEK_API_KEY
#
# Optional environment:
#   GHCR_OWNER      Default: weiha
#   IMAGE_TAG       Default: v0.1.0-alpha.1
#   API_SERVER_KEY  Generated if absent
#   SMOKE_PORT      Default: 18643
#   SMOKE_DIR       Default: $HOME/deepseek-native-agent-published-smoke

GHCR_OWNER="${GHCR_OWNER:-weiha}"
IMAGE_TAG="${IMAGE_TAG:-v0.1.0-alpha.1}"
IMAGE="ghcr.io/${GHCR_OWNER}/deepseek-native-agent"
REV="${REV:-1a8d29bd7075dcd71f52d2711c9f1d0fd7abf92c}"
SMOKE_PORT="${SMOKE_PORT:-18643}"
SMOKE_DIR="${SMOKE_DIR:-$HOME/deepseek-native-agent-published-smoke}"
CONTAINER_NAME="${CONTAINER_NAME:-deepseek-native-agent-alpha-smoke}"

if [[ -z "${DEEPSEEK_API_KEY:-}" ]]; then
  echo "DEEPSEEK_API_KEY is required." >&2
  exit 2
fi

if [[ -z "${API_SERVER_KEY:-}" ]]; then
  API_SERVER_KEY="$(openssl rand -hex 32)"
fi

docker pull "${IMAGE}:${IMAGE_TAG}"
image_rev="$(docker image inspect "${IMAGE}:${IMAGE_TAG}" --format '{{ index .Config.Labels "org.opencontainers.image.revision" }}')"
if [[ "$image_rev" != "$REV" ]]; then
  echo "Unexpected image revision: ${image_rev}" >&2
  echo "Expected: ${REV}" >&2
  exit 3
fi

rm -rf "$SMOKE_DIR"
mkdir -p "$SMOKE_DIR"
cp -a deploy "$SMOKE_DIR/"
cd "$SMOKE_DIR/deploy"

cp .env.example .env
python3 - <<PY
from pathlib import Path
path = Path(".env")
text = path.read_text(encoding="utf-8")
replacements = {
    "DEEPSEEK_API_KEY=\\n": "DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}\\n",
    "API_SERVER_KEY=\\n": "API_SERVER_KEY=${API_SERVER_KEY}\\n",
    "DEEPSEEK_NATIVE_IMAGE=deepseek-native-agent:latest\\n": "DEEPSEEK_NATIVE_IMAGE=${IMAGE}:${IMAGE_TAG}\\n",
    "DEEPSEEK_NATIVE_CONTAINER=deepseek-native-agent\\n": "DEEPSEEK_NATIVE_CONTAINER=${CONTAINER_NAME}\\n",
    "API_SERVER_PORT=8642\\n": "API_SERVER_PORT=${SMOKE_PORT}\\n",
}
for old, new in replacements.items():
    text = text.replace(old, new)
path.write_text(text, encoding="utf-8")
PY

mkdir -p data
cat > data/config.yaml <<'YAML'
model:
  provider: "deepseek"
  default: "deepseek-v4-flash"

deepseek_native:
  routing:
    enabled: true
    flash_model: "deepseek-v4-flash"
    pro_model: "deepseek-v4-pro"
  telemetry:
    enabled: true

gateway:
  platform_toolsets:
    api_server: [hermes-api-server]
    feishu: [hermes-feishu]
YAML

python3 validate_compose.py
docker compose --env-file .env config >/dev/null
docker compose --env-file .env up -d --no-build --pull never

for _ in $(seq 1 40); do
  if curl -fsS "http://127.0.0.1:${SMOKE_PORT}/health" >/tmp/deepseek-native-agent-health.json; then
    cat /tmp/deepseek-native-agent-health.json
    break
  fi
  sleep 2
done

curl -fsS \
  -H "Authorization: Bearer ${API_SERVER_KEY}" \
  -H "Content-Type: application/json" \
  "http://127.0.0.1:${SMOKE_PORT}/v1/chat/completions" \
  -d '{"model":"deepseek-v4-flash","messages":[{"role":"user","content":"Please reply with OK only."}],"max_tokens":8}' \
  >/tmp/deepseek-native-agent-chat.json

python3 - <<'PY'
import json
from pathlib import Path
data = json.loads(Path("/tmp/deepseek-native-agent-chat.json").read_text(encoding="utf-8"))
content = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
usage = data.get("usage", {})
print("API_CHAT_CONTENT_OK", content.upper() == "OK")
print("API_CHAT_CONTENT_LEN", len(content))
print("API_CHAT_USAGE_KEYS", ",".join(sorted(usage.keys())))
if content.upper() != "OK":
    raise SystemExit(4)
PY

docker compose --env-file .env ps
docker compose --env-file .env logs --tail=120 deepseek-native-agent
