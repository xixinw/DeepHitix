#!/usr/bin/env bash
set -euo pipefail

# Build and push the v0.1.0-alpha.1 image from clean branch 5.
#
# Optional environment:
#   GHCR_OWNER          Default: weiha
#   GHCR_TOKEN          If set, login before pushing. If absent, use existing docker login state.
#   IMAGE_TAG           Default: v0.1.0-alpha.1
#   IMAGE_ALIAS         Default: public-alpha

GHCR_OWNER="${GHCR_OWNER:-weiha}"
IMAGE="ghcr.io/${GHCR_OWNER}/deepseek-native-agent"
IMAGE_TAG="${IMAGE_TAG:-v0.1.0-alpha.1}"
IMAGE_ALIAS="${IMAGE_ALIAS:-public-alpha}"
REV="${REV:-1a8d29bd7075dcd71f52d2711c9f1d0fd7abf92c}"

if [[ -d .git ]]; then
  actual_rev="$(git rev-parse HEAD)"
elif [[ -f SOURCE_COMMIT.txt ]]; then
  actual_rev="$(cat SOURCE_COMMIT.txt)"
else
  echo "Cannot determine source revision; missing .git and SOURCE_COMMIT.txt." >&2
  exit 3
fi

if [[ "$actual_rev" != "$REV" ]]; then
  echo "Unexpected source revision: $actual_rev" >&2
  echo "Expected: $REV" >&2
  exit 3
fi

if [[ -n "${GHCR_TOKEN:-}" ]]; then
  echo "$GHCR_TOKEN" | docker login ghcr.io -u "$GHCR_OWNER" --password-stdin
else
  echo "GHCR_TOKEN is not set; using existing docker login state for ghcr.io."
fi

docker build \
  -f scripts/release/Dockerfile.public-alpha \
  --build-arg "HERMES_BASE_IMAGE=${HERMES_BASE_IMAGE:-nousresearch/hermes-agent:latest}" \
  --build-arg "PIP_INDEX_URL=${PIP_INDEX_URL:-}" \
  --build-arg "PIP_EXTRA_INDEX_URL=${PIP_EXTRA_INDEX_URL:-}" \
  --label "org.opencontainers.image.title=DeepSeek Native Agent" \
  --label "org.opencontainers.image.revision=$REV" \
  -t "${IMAGE}:${IMAGE_TAG}" \
  -t "${IMAGE}:${IMAGE_ALIAS}" \
  .

docker run --rm --entrypoint /opt/hermes/.venv/bin/python3 "${IMAGE}:${IMAGE_TAG}" - <<'PY'
import importlib.util
required = ["lark_oapi", "qrcode", "agent.routing_policy", "agent.cost_telemetry"]
missing = [name for name in required if importlib.util.find_spec(name) is None]
if missing:
    raise SystemExit(f"missing modules: {missing}")
print("IMAGE_IMPORT_PROBE_PASS")
PY

docker push "${IMAGE}:${IMAGE_TAG}"
docker push "${IMAGE}:${IMAGE_ALIAS}"
docker buildx imagetools inspect "${IMAGE}:${IMAGE_TAG}"
