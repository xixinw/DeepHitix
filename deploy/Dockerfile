# DeepSeek Native Agent image layer.
#
# This keeps the runtime close to upstream Hermes while productizing the Feishu
# optional dependency gap found during the Docker smoke: the stock upstream image
# does not include lark-oapi/qrcode, so a Feishu-enabled deployment must not rely
# on manual in-container installs.

ARG HERMES_BASE_IMAGE=nousresearch/hermes-agent:latest
FROM ${HERMES_BASE_IMAGE}

USER root

ARG PIP_INDEX_URL=
ARG PIP_EXTRA_INDEX_URL=

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

RUN set -eux; \
    pip_args=""; \
    if [ -n "${PIP_INDEX_URL}" ]; then pip_args="$pip_args --index-url ${PIP_INDEX_URL}"; fi; \
    if [ -n "${PIP_EXTRA_INDEX_URL}" ]; then pip_args="$pip_args --extra-index-url ${PIP_EXTRA_INDEX_URL}"; fi; \
    uv pip install --python /opt/hermes/.venv/bin/python3 $pip_args \
      "lark-oapi==1.5.3" \
      "qrcode==7.4.2"; \
    /opt/hermes/.venv/bin/python3 - <<'PY'
import importlib.util
missing = [name for name in ("lark_oapi", "qrcode") if importlib.util.find_spec(name) is None]
if missing:
    raise SystemExit(f"missing Feishu dependency modules: {missing}")
print("Feishu optional dependencies available")
PY

USER hermes
