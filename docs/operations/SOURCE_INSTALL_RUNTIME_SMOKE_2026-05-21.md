# Source Install Runtime Smoke - 2026-05-21

Purpose: verify the source-first DeepHitix alpha path from a clean Linux install directory.

## Result

PASS with corrected source install command.

```text
source package commit: 1a8d29bd7075dcd71f52d2711c9f1d0fd7abf92c
host: Ubuntu 24.04, Python 3.12.3
install directory: /home/ubuntu/deepseek-native-agent-install-smoke-corrected
runtime directory: /home/ubuntu/deepseek-native-agent-runtime-smoke-corrected
API bind: 127.0.0.1:18644
```

## Commands Verified

```bash
sudo apt-get install -y python3.12-venv
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -U pip
python -m pip install -e ".[web,homeassistant]"
```

## Runtime Checks

```text
IMPORT_CHECK=PASS
GET /health=PASS
GET /v1/models=PASS
```

Health response:

```json
{"status": "ok", "platform": "hermes-agent"}
```

Models response shape:

```json
{"object": "list", "data": [{"id": "hermes-agent", "object": "model"}]}
```

## Issues Found And Fixed

The previous README install command used:

```bash
uv pip install -e ".[web]"
```

Problems found during real install:

```text
Ubuntu hosts may lack python3.12-venv by default.
[web] installs FastAPI/Uvicorn but not aiohttp.
The API server adapter requires aiohttp, otherwise gateway logs:
  API Server: aiohttp not installed
```

Corrected README command:

```bash
python -m pip install -e ".[web,homeassistant]"
```

`homeassistant` is used here as the existing extra that pulls `aiohttp==3.13.3`; no Home Assistant configuration is enabled by this smoke.

## Cleanup

The smoke gateway process was stopped after verification. The existing server Hermes container remained healthy and untouched.
