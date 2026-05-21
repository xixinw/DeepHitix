# Docker + Feishu Smoke — 2026-05-19

## Scope

Target: Tencent Cloud Ubuntu host `101.34.214.32`.

Smoke goal from `CROSS_DIALOG_CONTINUATION.md`:

1. Docker-enabled Linux host prerequisites.
2. `deploy/install.sh`.
3. `docker compose config/up`.
4. API `/health`.
5. Feishu WebSocket connection.
6. Feishu message reply path.

## Result summary

| Check | Result | Evidence |
|---|---|---|
| Docker installed | PASS | `Docker version 29.1.3`, `Docker Compose version 2.40.3` |
| Docker registry access | PASS after mirror | `/etc/docker/daemon.json` uses `https://mirror.ccs.tencentyun.com`; `docker pull hello-world:latest` passed |
| `deploy/install.sh` syntax | PASS | `bash -n deploy/install.sh` passed locally |
| Compose static validation | PASS | `python deploy/validate_compose.py` passed locally and on Linux host |
| `docker compose config` | PASS | Config parsed with API server enabled, Feishu enabled, Telegram/Weixin disabled |
| Container start | PASS | `docker compose --env-file .env up -d` created and started `deepseek-native-agent` |
| Health endpoint | PASS | `curl http://127.0.0.1:18642/health` returned `{"status":"ok","platform":"hermes-agent"}` |
| Docker healthcheck | PASS after patch | Container state: `running healthy`; health log exit code `0` |
| API chat smoke | PASS after runtime config patch | `/v1/chat/completions` returned HTTP 200 and assistant content `OK` |
| Feishu WebSocket | PASS with productized Feishu image layer | `/health/detailed` showed `feishu: connected`; logs showed Lark WebSocket connected |
| Feishu inbound reply | PASS | Human-originated Feishu DM was received by the Docker smoke container, processed by the gateway, and a 2-char response was sent back to the same Feishu chat. Evidence from `/opt/data/logs/gateway.log`: raw message `om_x100b6ff752088888c2efda2fa3e6f41`, inbound user message, `response ready`, and `[Feishu] Sending response (2 chars)`. |
| Gateway user authorization env passthrough | PASS for smoke | `GATEWAY_ALLOW_ALL_USERS` added to compose/env example and used only for this one-off smoke; production should prefer `FEISHU_ALLOWED_USERS`. |
| Feishu optional dependency productization | PASS | Added `deploy/Dockerfile` and compose `build:` layer; remote build with `PIP_INDEX_URL=https://mirrors.tencent.com/pypi/simple` installed `lark-oapi==1.5.3`, `qrcode==7.4.2`, and import probe returned `FEISHU_DEPS_IMPORT_PASS`. |

## Exact commands/evidence snippets

Local gate before Linux smoke:

```text
python -m pytest tests/hermes_cli/test_deepseek_native_config.py tests/agent/test_routing_policy.py tests/agent/test_run_agent_cost_telemetry.py tests/agent/test_cost_telemetry.py tests/agent/test_usage_pricing.py tests/agent/test_auxiliary_main_first.py tests/agent/test_context_compressor.py tests/run_agent/test_deepseek_auxiliary_runtime.py tests/run_agent/test_plugin_context_engine_init.py -q -n 0
139 passed in 17.52s
```

Docker/Compose host state:

```text
Docker version 29.1.3, build 29.1.3-0ubuntu3~24.04.2
Docker Compose version 2.40.3+ds1-0ubuntu1~24.04.1
ServerVersion=29.1.3 Mirrors=["https://mirror.ccs.tencentyun.com/"]
```

Compose config smoke:

```text
FEISHU_ENABLED: "true"
HERMES_INFERENCE_PROVIDER: deepseek
HERMES_MODEL: deepseek-v4-flash
TELEGRAM_ENABLED: "false"
WEIXIN_ENABLED: "false"
published: "18642"
```

API health and detailed health:

```text
GET /health -> {"status": "ok", "platform": "hermes-agent"}
GET /health/detailed -> ok running connected connected
# fields: status, gateway_state, api_server state, feishu state
```

API chat:

```text
POST /v1/chat/completions -> HTTP_CODE=200
content=OK
usage_keys=completion_tokens,prompt_tokens,total_tokens
```

Feishu WebSocket:

```text
[Lark] [INFO] connected to wss://msg-frontier.feishu.cn/ws/v2 ... [conn_id=...]
```

Feishu human-origin inbound reply path:

```text
2026-05-19 09:47:57,253 INFO gateway.platforms.feishu: [Feishu] Received raw message type=text message_id=om_x100b6ff752088888c2efda2fa3e6f41
2026-05-19 09:47:57,254 INFO gateway.platforms.feishu: [Feishu] Inbound dm message received: id=om_x100b6ff752088888c2efda2fa3e6f41 type=text chat_id=oc_790a7dd8de153a70c149887d1d4eba56 sender=user:ou_39711248eae9d16cc66eec24ce29cbad text='请只回复 OK，来自 Docker smoke' media=0
2026-05-19 09:47:59,560 INFO gateway.run: inbound message: platform=feishu user=用户193606 chat=oc_790a7dd8de153a70c149887d1d4eba56 msg='请只回复 OK，来自 Docker smoke'
2026-05-19 09:51:15,200 INFO gateway.run: response ready: platform=feishu chat=oc_790a7dd8de153a70c149887d1d4eba56 time=195.6s api_calls=1 response=2 chars
2026-05-19 09:51:15,221 INFO gateway.platforms.base: [Feishu] Sending response (2 chars) to oc_790a7dd8de153a70c149887d1d4eba56
```

Why this counts:

- The message is human-originated (`sender=user:...`), not a bot/self-sent message.
- The gateway created a normal inbound event for platform `feishu`.
- The agent produced a response with one API call.
- The Feishu adapter sent the response to the same chat ID.

Docker healthcheck:

```text
running healthy
Health.Log ExitCode: 0
```

## Issues found and fixed in deploy assets

### 1. `HERMES_PROVIDER` did not drive gateway runtime provider

Observed API request failure before patch:

```text
provider=deepseek model=anthropic/claude-opus-4.6
The supported API model names are deepseek-v4-pro or deepseek-v4-flash, but you passed anthropic/claude-opus-4.6.
```

Cause:

- Gateway runtime provider resolver reads `HERMES_INFERENCE_PROVIDER`.
- Gateway model resolver reads `config.yaml`, not `HERMES_MODEL` directly.
- Empty container data volume bootstrapped the generic upstream config, so model stayed at the image default while provider became DeepSeek.

Fix applied:

- `deploy/docker-compose.yml`: changed provider env to `HERMES_INFERENCE_PROVIDER`.
- `deploy/.env.example`: changed `HERMES_PROVIDER=deepseek` to `HERMES_INFERENCE_PROVIDER=deepseek`.
- `deploy/install.sh`: now materializes `deploy/data/config.yaml` before first container boot with:
  - `model.provider: deepseek`
  - `model.default: deepseek-v4-flash`
  - `deepseek_native.routing.enabled: true`
  - API/Feishu platform toolsets.

### 2. Docker healthcheck used `python`, but image only exposes `python3`

Observed Docker healthcheck failure:

```text
/bin/sh: 1: python: not found
```

Fix applied:

- `deploy/docker-compose.yml` healthcheck now uses `python3`.

### 3. Stock upstream image lacks Feishu optional dependencies — productized

Observed before workaround:

```text
WARNING gateway.run: Feishu: lark-oapi not installed or FEISHU_APP_ID/SECRET not set
WARNING gateway.run: No adapter available for feishu
```

Confirmed cause:

- `lark_oapi` and `qrcode` were absent inside `nousresearch/hermes-agent:latest`.
- `pyproject.toml` declares `feishu = ["lark-oapi==1.5.3", "qrcode==7.4.2"]`, but `[all]` intentionally excludes Feishu and relies on lazy-install paths. Gateway Feishu adapter creation did not lazy-install before `check_feishu_requirements()`.

Original smoke workaround used:

1. Downloaded Feishu wheels on the host from Tencent PyPI mirror.
2. Installed into the running container venv.
3. Committed a local smoke-only image: `deepseek-native-agent:feishu-smoke`.
4. Recreated compose using that local image.

Product-grade fix now applied:

- `deploy/Dockerfile` extends `nousresearch/hermes-agent:latest` and installs `lark-oapi==1.5.3` / `qrcode==7.4.2` into `/opt/hermes/.venv` using `uv pip`.
- `deploy/docker-compose.yml` builds the thin project image layer by default.
- `deploy/install.sh` runs `docker compose build deepseek-native-agent` before service start.
- `deploy/.env.example` exposes `HERMES_BASE_IMAGE`, `PIP_INDEX_URL`, and `PIP_EXTRA_INDEX_URL` for mirror-controlled builds.
- `deploy/.dockerignore` excludes `.env`, runtime data, logs, and key material from Docker build context.

Remote verification:

```text
PIP_INDEX_URL=https://mirrors.tencent.com/pypi/simple docker compose --env-file .env build deepseek-native-agent
Installed 5 packages: lark-oapi==1.5.3, pycryptodome==3.23.0, pypng==0.20220715.0, qrcode==7.4.2, requests-toolbelt==1.0.0
Feishu optional dependencies available
docker run --rm --entrypoint /opt/hermes/.venv/bin/python3 deepseek-native-agent:feishu-smoke -c "import lark_oapi, qrcode; print('FEISHU_DEPS_IMPORT_PASS')"
FEISHU_DEPS_IMPORT_PASS
```

### 4. `GATEWAY_ALLOW_ALL_USERS` was not passed through compose

Observed after enabling Feishu:

```text
WARNING gateway.run: No user allowlists configured. All unauthorized users will be denied.
Set GATEWAY_ALLOW_ALL_USERS=true in ~/.hermes/.env to allow open access...
```

Cause:

- The smoke `.env` had no user allowlist by default.
- Compose also did not pass `GATEWAY_ALLOW_ALL_USERS` into the container, so a temporary smoke override could not reach the gateway.

Fix applied:

- `deploy/docker-compose.yml`: added `GATEWAY_ALLOW_ALL_USERS: ${GATEWAY_ALLOW_ALL_USERS:-false}`.
- `deploy/.env.example`: documented `GATEWAY_ALLOW_ALL_USERS=false` and noted production should prefer `FEISHU_ALLOWED_USERS`.

## Current remote smoke state

- Smoke directory: `/home/ubuntu/deepseek-native-agent-smoke`
- Compose file: `/home/ubuntu/deepseek-native-agent-smoke/deploy/docker-compose.yml`
- Env file: `/home/ubuntu/deepseek-native-agent-smoke/deploy/.env` (contains secrets; do not print)
- Data dir: `/home/ubuntu/deepseek-native-agent-smoke/deploy/data`
- Local smoke image: `deepseek-native-agent:feishu-smoke`
- Published host port: `127.0.0.1:18642 -> container:8642`
- Current smoke auth mode: `.env` has `GATEWAY_ALLOW_ALL_USERS=true` only to make the one-off inbound test possible. Do not carry that into production without another access boundary.
- Existing production Hermes gateway on the host was not stopped; smoke used port `18642` to avoid conflict with `8642`.

## Remaining work

1. Move to Phase 5: release packaging/README polish/upstream PR branch preparation.
2. Keep Feishu platform scope isolated; do not expand to Telegram/Weixin/WeCom matrix until Phase 5 packaging is coherent.

## Do not overclaim

This smoke proves Docker install/config/up, health, API chat, Feishu WebSocket connection, one human-origin Feishu DM reply path, and a reproducible project image layer that installs Feishu optional dependencies. It does not yet prove a published registry image tag; that belongs to Phase 5 release packaging.
