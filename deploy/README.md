# Docker Compose validation base

This directory contains the first reproducible deployment base for DeepSeek Native Agent.

It is not the final production deployment. It is the smoke-test foundation for:

1. API server availability
2. DeepSeek provider configuration
3. future community Web UI connection
4. later Linux install.sh and systemd examples
5. Feishu gateway deployment via `docs/operations/FEISHU_DEPLOYMENT.md`

## Files

```text
deploy/
├── docker-compose.yml
├── Dockerfile
├── .dockerignore
├── .env.example
├── README.md
└── validate_compose.py
```

## Quick start

```bash
cd deploy
cp .env.example .env
# edit .env and fill DEEPSEEK_API_KEY + API_SERVER_KEY
docker compose config
docker compose build deepseek-native-agent
docker compose up -d
docker compose logs -f deepseek-native-agent
```

Health check target:

```bash
curl http://127.0.0.1:8642/health
```

If API auth is required by the endpoint you test, pass:

```bash
curl -H "Authorization: Bearer $API_SERVER_KEY" http://127.0.0.1:8642/health
```

## Defaults

The compose base is intentionally conservative:

- API server is enabled as the smoke-test surface.
- API server binds to `127.0.0.1` by default.
- Telegram and Weixin are explicitly disabled.
- Feishu is disabled by default and will be enabled only in the Feishu deployment guide.
- The image layer installs Feishu optional dependencies (`lark-oapi`, `qrcode`) so Feishu can work when enabled without manual container mutation.
- Data persists under `deploy/data` by default and is mounted to `/opt/data` in the container.

## Required variables

Set these in `deploy/.env`:

```text
DEEPSEEK_API_KEY=...
API_SERVER_KEY=...
```

Generate `API_SERVER_KEY` with one of:

```bash
openssl rand -hex 32
python - <<'PY'
import secrets
print(secrets.token_hex(32))
PY
```

## Static validation

On machines without Docker, run:

```bash
python validate_compose.py
```

This checks that:

- `docker-compose.yml` exists and parses as YAML if PyYAML is installed;
- required services and files are present;
- obvious unsafe defaults are not enabled;
- Telegram is not enabled in the smoke base;
- local absolute paths are not hard-coded.

## Security notes

- Do not commit `deploy/.env`.
- Do not expose port `8642` to the public internet directly.
- Put public deployments behind reverse proxy auth/TLS.
- Keep chat platforms disabled until their guide has a dedicated verification path.

## Image layer

This compose base builds a thin project-owned image by default:

```text
DEEPSEEK_NATIVE_IMAGE=deepseek-native-agent:latest
HERMES_BASE_IMAGE=nousresearch/hermes-agent:latest
```

The Dockerfile extends upstream Hermes and installs the Feishu optional dependencies (`lark-oapi==1.5.3`, `qrcode==7.4.2`) into `/opt/hermes/.venv` using `uv pip`. This closes the smoke gap where `nousresearch/hermes-agent:latest` could connect API server but could not create the Feishu adapter without manual package installs.

`.dockerignore` excludes `deploy/.env`, runtime data, logs, and key material from the Docker build context. Do not remove it; secrets should never be sent to the Docker daemon during image builds.

For restricted networks, set one of:

```text
PIP_INDEX_URL=https://mirror.example/simple
PIP_EXTRA_INDEX_URL=https://pypi.org/simple
```

The env variables named `DEEPSEEK_NATIVE_*` document the wrapper profile contract. The Linux install script also materializes equivalent settings into `/opt/data/config.yaml` before first boot so the gateway does not inherit a non-DeepSeek default model from the upstream image.

## Published image smoke

For the public alpha registry smoke, do not rely on a local build cache. Use the release tag documented in:

```text
../docs/operations/PUBLISHED_IMAGE_SMOKE_2026-05-21.md
```

The smoke path should pull the published image first, set:

```text
DEEPSEEK_NATIVE_IMAGE=ghcr.io/weiha/deepseek-native-agent:v0.1.0-alpha.1
```

Then start compose with:

```bash
docker compose --env-file .env up -d --no-build --pull never
```

This keeps the verification honest: the container must come from the registry tag, not from the local Docker build cache.

