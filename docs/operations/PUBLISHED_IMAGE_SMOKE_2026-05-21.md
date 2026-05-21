# Published Image Docker Smoke Plan / Blocked Execution - 2026-05-21

Purpose: define the Phase 5 release image name/tag and the exact smoke path for a registry-published Docker image. This is not a success report yet.

## Current decision

Use GHCR unless the user chooses another registry:

```text
registry namespace: ghcr.io/weiha
image name:         ghcr.io/weiha/deepseek-native-agent
immutable tag:     v0.1.0-alpha.1
moving alpha tag:  public-alpha
source commit:     1a8d29bd7075dcd71f52d2711c9f1d0fd7abf92c
source branch:     deepseek-native/0005-cache-observability-hash-prefix-drift-clean
```

Rationale:

- `v0.1.0-alpha.1` is an immutable SemVer-style first public alpha tag.
- `public-alpha` is a human-friendly moving alias for README quick starts after the immutable tag is verified.
- The image name avoids using `nousresearch/hermes-agent`, which would imply upstream ownership or official status.
- Default owner is set to `weiha` for Phase 5 execution. If the actual GitHub/GHCR owner differs, update the namespace before publishing.

## Important packaging finding

The release image must be built from the clean branch 5 source, not only from `deploy/Dockerfile`.

`deploy/Dockerfile` currently extends an existing Hermes image and installs Feishu optional dependencies. It does not copy the DeepSeek-native branch code into the image. Therefore, the v0.1.0-alpha.1 release build uses `scripts/release/Dockerfile.public-alpha` to overlay the clean branch 5 source onto `nousresearch/hermes-agent:latest`, install the editable project into the existing Hermes venv, and install Feishu optional dependencies.

This avoids a full upstream production-image rebuild on a small smoke host while still ensuring the published image contains the DeepSeek-native code under test.

## Current publishing status

Remote build execution has now reached the registry boundary:

```text
remote image build: PASS
local image import probe: PASS
push to GHCR: BLOCKED
published-image pull smoke: NOT RUN
```

Evidence is recorded in:

```text
docs/operations/PUBLISHED_IMAGE_BUILD_ATTEMPT_2026-05-21.md
```

Publishing is blocked because the GHCR login token on the Linux host does not have the package scopes required to push `ghcr.io/weiha/deepseek-native-agent`.

Second token check on 2026-05-21:

```text
GitHub API identity check: PASS
GHCR docker login: FAIL
reported token scopes: repo
missing scopes: read:packages, write:packages
```

Third token check on 2026-05-21 for `xixinw`:

```text
GitHub API identity check: PASS
reported token scopes include write:packages: YES
reported token scopes include read:packages: NO
GHCR docker login: FAIL
```

Fourth token check on 2026-05-21 for `xixinw`:

```text
GitHub API identity check: PASS
reported token scopes include write:packages: YES
reported token scopes include read:packages: NO
GHCR docker login: FAIL
```

Minimum credential required for GHCR:

```bash
export GHCR_OWNER=weiha
export GHCR_TOKEN=<classic-pat-or-fine-grained-token-with-write-packages>
echo "$GHCR_TOKEN" | docker login ghcr.io -u "$GHCR_OWNER" --password-stdin
```

## Build and push commands

Run these on a Linux Docker host from a clean checkout of the release source:

```bash
set -euo pipefail

IMAGE="ghcr.io/weiha/deepseek-native-agent"
TAG="v0.1.0-alpha.1"
ALIAS="public-alpha"
REV="1a8d29bd7075dcd71f52d2711c9f1d0fd7abf92c"

git switch deepseek-native/0005-cache-observability-hash-prefix-drift-clean
git rev-parse HEAD
test "$(git rev-parse HEAD)" = "$REV"

docker build \
  -f scripts/release/Dockerfile.public-alpha \
  --build-arg HERMES_BASE_IMAGE=nousresearch/hermes-agent:latest \
  --label "org.opencontainers.image.title=DeepSeek Native Agent" \
  --label "org.opencontainers.image.revision=$REV" \
  -t "$IMAGE:$TAG" \
  -t "$IMAGE:$ALIAS" \
  .

docker run --rm --entrypoint /opt/hermes/.venv/bin/python3 "$IMAGE:$TAG" - <<'PY'
import importlib.util
required = ["lark_oapi", "qrcode", "agent.routing_policy", "agent.cost_telemetry"]
missing = [name for name in required if importlib.util.find_spec(name) is None]
if missing:
    raise SystemExit(f"missing modules: {missing}")
print("IMAGE_IMPORT_PROBE_PASS")
PY

docker push "$IMAGE:$TAG"
docker push "$IMAGE:$ALIAS"
docker buildx imagetools inspect "$IMAGE:$TAG"
```

## Published-image smoke commands

Run these on a Linux Docker host that has no local image build cache dependency. If possible, use a different host from the build host.

```bash
set -euo pipefail

export IMAGE="ghcr.io/weiha/deepseek-native-agent"
export TAG="v0.1.0-alpha.1"
export REV="1a8d29bd7075dcd71f52d2711c9f1d0fd7abf92c"
export SMOKE_DIR="$HOME/deepseek-native-agent-published-smoke"

# Required before editing .env:
# export DEEPSEEK_API_KEY=...
# export API_SERVER_KEY="$(openssl rand -hex 32)"

rm -rf "$SMOKE_DIR"
git clone <release-repo-url> "$SMOKE_DIR"
cd "$SMOKE_DIR"

docker pull "$IMAGE:$TAG"
docker image inspect "$IMAGE:$TAG" --format '{{ index .Config.Labels "org.opencontainers.image.revision" }}'
test "$(docker image inspect "$IMAGE:$TAG" --format '{{ index .Config.Labels "org.opencontainers.image.revision" }}')" = "$REV"

cd deploy
cp .env.example .env
python3 - <<'PY'
import os
from pathlib import Path
p = Path(".env")
text = p.read_text()
text = text.replace("DEEPSEEK_API_KEY=\n", f"DEEPSEEK_API_KEY={os.environ['DEEPSEEK_API_KEY']}\n")
text = text.replace("API_SERVER_KEY=\n", f"API_SERVER_KEY={os.environ['API_SERVER_KEY']}\n")
text = text.replace("DEEPSEEK_NATIVE_IMAGE=deepseek-native-agent:latest\n", f"DEEPSEEK_NATIVE_IMAGE={os.environ['IMAGE']}:{os.environ['TAG']}\n")
text = text.replace("API_SERVER_PORT=8642\n", "API_SERVER_PORT=18642\n")
p.write_text(text)
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

# Critical: use the pulled published tag. Do not build.
docker compose --env-file .env up -d --no-build --pull never

for i in $(seq 1 30); do
  if curl -fsS http://127.0.0.1:18642/health; then
    break
  fi
  sleep 2
done

docker compose --env-file .env ps
docker compose --env-file .env logs --tail=120 deepseek-native-agent
```

API chat smoke:

```bash
curl -fsS \
  -H "Authorization: Bearer $API_SERVER_KEY" \
  -H "Content-Type: application/json" \
  http://127.0.0.1:18642/v1/chat/completions \
  -d '{
    "model": "deepseek-v4-flash",
    "messages": [{"role": "user", "content": "Please reply with OK only."}]
  }'
```

Feishu smoke, only if credentials and a human tester are available:

```text
Set FEISHU_ENABLED=true, FEISHU_APP_ID, FEISHU_APP_SECRET, FEISHU_ALLOWED_USERS or a temporary GATEWAY_ALLOW_ALL_USERS=true for one-off smoke only.
Restart compose with --no-build.
Verify /health/detailed shows feishu connected.
Send a human-origin Feishu DM and confirm logs show inbound message, response ready, and Feishu send response to the same chat.
```

## Verification completed in this session

Local/static and remote release-candidate verification completed:

```text
clean branch 5 gate: 170 passed in 16.05s
deploy/validate_compose.py: PASS
real DeepSeek API smoke: PASS
remote release candidate image build: PASS
remote local image import probe: PASS
GHCR push: BLOCKED by token scope mismatch
```

No published image success is claimed yet.

## Minimum success criteria for closing this task

One of these must be true before reporting release success:

1. `ghcr.io/weiha/deepseek-native-agent:v0.1.0-alpha.1` exists, is pulled on a Linux host, and `/health` plus API chat pass with `--no-build`; or
2. The task remains blocked with the missing registry/host credentials listed above.

